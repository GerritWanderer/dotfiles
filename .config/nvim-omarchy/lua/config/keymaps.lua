-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
vim.keymap.set('n', '<C-h>', require('smart-splits').move_cursor_left)
vim.keymap.set('n', '<C-j>', require('smart-splits').move_cursor_down)
vim.keymap.set('n', '<C-k>', require('smart-splits').move_cursor_up)
vim.keymap.set('n', '<C-l>', require('smart-splits').move_cursor_right)

-- Delete all marks (a-z, A-Z) on the current line (no built-in equivalent;
-- `m-` mirrors the vim-signature convention)
vim.keymap.set("n", "m-", function()
  local buf = vim.api.nvim_get_current_buf()
  local line = vim.api.nvim_win_get_cursor(0)[1]
  local deleted = {}
  for c = ("a"):byte(), ("z"):byte() do
    local name = string.char(c)
    if vim.api.nvim_buf_get_mark(buf, name)[1] == line then
      vim.api.nvim_buf_del_mark(buf, name)
      table.insert(deleted, name)
    end
  end
  for c = ("A"):byte(), ("Z"):byte() do
    local name = string.char(c)
    local m = vim.api.nvim_get_mark(name, {})
    if m[1] == line and m[3] == buf then
      vim.api.nvim_del_mark(name)
      table.insert(deleted, name)
    end
  end
  if #deleted > 0 then
    vim.notify("Deleted marks: " .. table.concat(deleted, " "))
  end
end, { desc = "Delete marks on current line" })
