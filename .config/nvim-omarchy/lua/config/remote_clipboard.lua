-- Clipboard for sessions whose yanks may need to reach another machine:
-- every copy is emitted as OSC 52 (inside tmux this becomes a tmux buffer,
-- rebroadcast to every attached client, local or SSH). Paste prefers the
-- local Wayland clipboard when one is available, so content copied in other
-- apps remains pasteable; in tmux, paste reads the tmux buffer; otherwise,
-- paste uses an in-memory session cache to avoid OSC 52 query timeouts (which
-- terminals do not answer).
local M = {}

local function proc_lines(pid, file)
  local ok, lines = pcall(vim.fn.readfile, "/proc/" .. pid .. "/" .. file)
  return ok and lines or {}
end

local function proc_ppid(pid)
  for _, line in ipairs(proc_lines(pid, "status")) do
    local ppid = line:match("^PPid:%s+(%d+)")
    if ppid then
      return tonumber(ppid)
    end
  end
end

local function ancestor_process_named(name)
  local pid = vim.fn.getpid()

  for _ = 1, 16 do
    local ppid = proc_ppid(pid)
    if not ppid or ppid <= 1 then
      return false
    end

    local comm = proc_lines(ppid, "comm")[1] or ""
    if comm:find(name, 1, true) then
      return true
    end

    pid = ppid
  end

  return false
end

function M.setup()
  local in_tmux = vim.env.TMUX ~= nil
  local in_ssh = vim.env.SSH_TTY ~= nil or vim.env.SSH_CONNECTION ~= nil
  local in_herdr = vim.env.HERDR_PANE_ID ~= nil or ancestor_process_named("herdr")

  if not (in_tmux or in_ssh or in_herdr) then
    return
  end

  local osc52 = require("vim.ui.clipboard.osc52")
  local has_wayland = vim.env.WAYLAND_DISPLAY ~= nil
    and vim.fn.executable("wl-copy") == 1
    and vim.fn.executable("wl-paste") == 1

  local cache = {
    ["+"] = { {}, "" },
    ["*"] = { {}, "" },
  }

  local function copy(register)
    local emit = osc52.copy(register)

    return function(lines, regtype)
      regtype = regtype or ""
      cache[register] = { lines, regtype }
      if register == "+" then
        cache["*"] = { lines, regtype }
      elseif register == "*" then
        cache["+"] = { lines, regtype }
      end

      if has_wayland then
        local cmd = { "wl-copy", "--sensitive", "--type", "text/plain" }
        if register == "*" then
          cmd[#cmd + 1] = "--primary"
        end
        vim.fn.system(cmd, lines)
      end

      if in_tmux and vim.fn.executable("tmux") == 1 then
        vim.fn.system({ "tmux", "load-buffer", "-" }, lines)
      end

      if vim.g.omarchy_remote_clipboard_osc52 ~= false then
        emit(lines)
      end
    end
  end

  local function paste(register)
    return function()
      if has_wayland then
        local cmd = { "wl-paste", "--no-newline" }
        if register == "*" then
          cmd[#cmd + 1] = "--primary"
        end

        local lines = vim.fn.systemlist(cmd, "", 1)
        if vim.v.shell_error == 0 then
          return { lines, "v" }
        end
      end

      if in_tmux and vim.fn.executable("tmux") == 1 then
        local lines = vim.fn.systemlist({ "tmux", "save-buffer", "-" }, "", 1)
        if vim.v.shell_error == 0 and #lines > 0 then
          return { lines, "v" }
        end
      end

      if cache[register] and cache[register][1] and #cache[register][1] > 0 then
        return cache[register]
      end

      local reg0 = vim.fn.getreg("0", 1, true)
      if reg0 and #reg0 > 0 and (reg0[1] ~= "" or #reg0 > 1) then
        return { reg0, vim.fn.getregtype("0") }
      end

      return { {}, "" }
    end
  end

  vim.g.clipboard = {
    name = "OmarchyRemoteClipboard",
    copy = { ["+"] = copy("+"), ["*"] = copy("*") },
    paste = { ["+"] = paste("+"), ["*"] = paste("*") },
    cache_enabled = 0,
  }
end

return M
