local add = vim.pack.add
local later = Config.later

-- Snippets ===================================================================

-- Although 'mini.snippets' provides functionality to manage snippet files, it
-- deliberately doesn't come with those.
--
-- The 'rafamadriz/friendly-snippets' is currently the largest collection of
-- snippet files. They are organized in 'snippets/' directory (mostly) per language.
-- 'mini.snippets' is designed to work with it as seamlessly as possible.
-- See `:h MiniSnippets.gen_loader.from_lang()`.
later(function() add({ 'https://github.com/rafamadriz/friendly-snippets' }) end)

-- OSC ===================================================================
vim.g.clipboard = {
  name = 'OSC 52',
  copy = {
    ['+'] = require('vim.ui.clipboard.osc52').copy('+'),
    ['*'] = require('vim.ui.clipboard.osc52').copy('*'),
  },
  paste = {
    ['+'] = require('vim.ui.clipboard.osc52').paste('+'),
    ['*'] = require('vim.ui.clipboard.osc52').paste('*'),
  },
}


-- Obsidian ===================================================================

-- obsidian-nvim/obsidian.nvim is a community fork of the Obsidian plugin for
-- Neovim. It provides note navigation, daily notes, templates, backlinks, tags,
-- and more. Only active inside markdown files within the configured vault path.
--
-- Commands cheat sheet (all via `:Obsidian <Tab>` or the keymaps below):
--   Navigation:   <Leader>on (new from template)  <Leader>oq (quick switch)  <Leader>os (search)
--   Daily notes:  <Leader>ot (today)     <Leader>oT (today float)  <Leader>oy (yesterday)     <Leader>om (tomorrow)
--   Links:        <CR>       (smart act) [o / ]o    (prev/next link)
--   Note tools:   <Leader>ob (backlinks) <Leader>oc (toggle checkbox)
--                 <Leader>ol (links in note)  <Leader>od (daily list)
--                 <Leader>ow (switch workspace)
--   Templates:    <Leader>oi (insert template)
--   Visual:       <Leader>ox (extract selection to new note)  <Leader>ok (link selection)
later(function()
  add({ 'https://github.com/obsidian-nvim/obsidian.nvim' })

  ---@module 'obsidian'
  ---@type obsidian.config
  require('obsidian').setup({
    legacy_commands = false,

    workspaces = {
      {
        name = 'notes',
        path = '~/Documents/notes',
      },
    },

    -- New notes go into 01-Wildflowers by default
    notes_subdir = '01-Wildflowers',

    -- Slugify the title as note ID (e.g. "My Note" -> "my-note")
    note_id_func = function(title)
      return title:gsub(' ', '-'):gsub('[^A-Za-z0-9-]', ''):lower()
    end,

    -- Templates folder inside the vault
    templates = {
      folder = '99-extras/templates',
    },

    -- Use telescope for all picker actions
    picker = { name = 'snacks.nvim' },

    -- Open note in current window by default (change to 'vsplit' or 'hsplit' if preferred)
    open_notes_in = 'current',

    -- Daily notes configuration
    daily_notes = {
      folder = '00-Daily',
      date_format = '%Y/%m-%B/%Y-%m-%d-%A',
      default_tags = { 'type/daily' },
      template = 'daily',
    },

    -- Disable default UI extras (handled by treesitter in this config)
    ui = { enable = false },
  })

  -- Global shortcuts (work outside of note buffers too, e.g. from starter)
  vim.keymap.set('n', '<Leader>os', '<Cmd>Obsidian search<CR>',       { desc = 'Obsidian search vault' })
  vim.keymap.set('n', '<Leader>ot', '<Cmd>Obsidian today<CR>',        { desc = 'Obsidian today' })
  vim.keymap.set('n', '<Leader>od', '<Cmd>Obsidian dailies<CR>',      { desc = 'Obsidian daily list' })

  -- Open today's daily note in a Snacks floating window
  vim.keymap.set('n', '<Leader>oT', function()
    local note = require('obsidian.daily').today()
    Snacks.win.new({
      file     = tostring(note.path),
      position = 'float',
      width    = 0.7,
      height   = 0.8,
      border   = 'rounded',
      title    = ' Daily Note ',
      title_pos = 'center',
    })
  end, { desc = 'Obsidian today (float)' })
end)

