-- ┌─────────────────────────┐
-- │ Plugins outside of MINI │
-- └─────────────────────────┘
--
-- This file installs plugins outside of MINI.
-- Custom configuration lives in 'after/plugin/40_plugins.lua'.

local add = vim.pack.add
local now, now_if_args, later = Config.now, Config.now_if_args, Config.later

-- ┌─────────────────────────┐
-- │ Tree-sitter             │
-- └─────────────────────────┘
now_if_args(function()
  local ts_update = function() vim.cmd('TSUpdate') end
  Config.on_packchanged('nvim-treesitter', { 'update' }, ts_update, ':TSUpdate')

  add({
    'https://github.com/nvim-treesitter/nvim-treesitter',
    'https://github.com/nvim-treesitter/nvim-treesitter-textobjects',
  })

  local languages = {
    'lua', 'vimdoc', 'markdown',
    'javascript', 'typescript', 'tsx',
  }
  local isnt_installed = function(lang)
    return #vim.api.nvim_get_runtime_file('parser/' .. lang .. '.*', false) == 0
  end
  local to_install = vim.tbl_filter(isnt_installed, languages)
  if #to_install > 0 then require('nvim-treesitter').install(to_install) end

  local filetypes = {}
  for _, lang in ipairs(languages) do
    for _, ft in ipairs(vim.treesitter.language.get_filetypes(lang)) do
      table.insert(filetypes, ft)
    end
  end
  local ts_start = function(ev) vim.treesitter.start(ev.buf) end
  Config.new_autocmd('FileType', filetypes, ts_start, 'Start tree-sitter')
end)

-- ┌─────────────────────────┐
-- │ Language Servers        │
-- └─────────────────────────┘
now_if_args(function()
  add({ 'https://github.com/neovim/nvim-lspconfig' })
  vim.lsp.enable({
    'lua_ls',    -- Install: brew install lua-language-server
    'tsgo',      -- Install: npm install @typescript/native-preview
    -- 'ts_ls',  -- Install: npm install -g typescript typescript-language-server
    'eslint',    -- Install: npm install -g vscode-langservers-extracted
  })
end)

-- ┌─────────────────────────┐
-- │ Formatting              │
-- └─────────────────────────┘
later(function() add({ 'https://github.com/stevearc/conform.nvim' }) end)

-- ┌─────────────────────────┐
-- │ UI enhancements         │
-- └─────────────────────────┘
-- Must be set up before first draw to intercept startup messages.
-- See 'after/plugin/40_plugins.lua' for other plugin configurations.
now(function()
  add({
    'https://github.com/folke/noice.nvim',
    'https://github.com/MunifTanjim/nui.nvim',
  })
  require('noice').setup({
    notify = { enabled = true },
    lsp = {
      override = {
        ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
        ["vim.lsp.util.stylize_markdown"] = true,
        ["cmp.entry.get_documentation"] = true,
      },
    },
    routes = {
      {
        filter = {
          event = "msg_show",
          any = {
            { find = "%d+L, %d+B" },
            { find = "; after #%d+" },
            { find = "; before #%d+" },
          },
        },
        view = "mini",
      },
    },
    presets = {
      bottom_search = true,
      command_palette = true,
      long_message_to_split = true,
    },
  })
end)

-- ┌─────────────────────────┐
-- │ Color scheme            │
-- └─────────────────────────┘
now(function()
  add({ 'https://github.com/folke/tokyonight.nvim' })
  require('tokyonight').setup({ style = 'night' })
  vim.cmd('colorscheme tokyonight')
end)

-- ┌─────────────────────────┐
-- │ Snacks                  │
-- └─────────────────────────┘
later(function() add({ 'https://github.com/folke/snacks.nvim' }) end)

-- ┌─────────────────────────┐
-- │ Smart splits            │
-- └─────────────────────────┘
later(function() add({ 'https://github.com/mrjones2014/smart-splits.nvim' }) end)

-- ┌─────────────────────────┐
-- │ Completion              │
-- └─────────────────────────┘
later(function() add({ { src = 'https://github.com/Saghen/blink.cmp', version = 'v1.10.1' } }) end)

-- ┌─────────────────────────┐
-- │ Jump / navigation       │
-- └─────────────────────────┘
later(function() add({ 'https://github.com/folke/flash.nvim' }) end)
