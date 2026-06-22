-- ┌─────────────────┐
-- │ Custom mappings │
-- └─────────────────┘
--
-- This file contains definitions of custom general and Leader mappings.

-- General mappings ===========================================================

-- Use this section to add custom general mappings. See `:h vim.keymap.set()`.

-- An example helper to create a Normal mode mapping
local nmap = function(lhs, rhs, desc)
  -- See `:h vim.keymap.set()`
  vim.keymap.set('n', lhs, rhs, { desc = desc })
end

local remove_lsp_mapping = function(mode, lhs)
  local map_desc = vim.fn.maparg(lhs, mode, false, true).desc
  if map_desc == nil or string.find(map_desc, 'vim%.lsp') == nil then return end
  vim.keymap.del(mode, lhs)
end

-- Clear hlsearch on Escape (n, i, s modes - like LazyVim)
vim.keymap.set({ 'i', 's' }, '<Esc>', '<Esc><Cmd>nohlsearch<CR>', { desc = 'Escape and clear hlsearch' })
nmap('<Esc>', '<Esc><Cmd>nohlsearch<CR>', 'Escape and clear hlsearch')

-- Paste linewise before/after current line
-- Usage: `yiw` to yank a word and `]p` to put it on the next line.
nmap('[p', '<Cmd>exe "iput! " . v:register<CR>', 'Paste Above')
nmap(']p', '<Cmd>exe "iput "  . v:register<CR>', 'Paste Below')

-- Many general mappings are created by 'mini.basics'. See 'plugin/30_mini.lua'

-- stylua: ignore start
-- The next part (until `-- stylua: ignore end`) is aligned manually for easier
-- reading. Consider preserving this or remove `-- stylua` lines to autoformat.

-- Leader mappings ============================================================

-- Neovim has the concept of a Leader key (see `:h <Leader>`). It is a configurable
-- key that is primarily used for "workflow" mappings (opposed to text editing).
-- Like "open file explorer", "create scratch buffer", "pick from buffers".
--
-- In 'plugin/10_options.lua' <Leader> is set to <Space>, i.e. press <Space>
-- whenever there is a suggestion to press <Leader>.
--
-- This config uses a "two key Leader mappings" approach: first key describes
-- semantic group, second key executes an action. Both keys are usually chosen
-- to create some kind of mnemonic.
-- Example: `<Leader>f` groups "find" type of actions; `<Leader>ff` - find files.
-- Use this section to add Leader mappings in a structural manner.
--
-- Usually if there are global and local kinds of actions, lowercase second key
-- denotes global and uppercase - local.
-- Example: `<Leader>fs` / `<Leader>fS` - find workspace/document LSP symbols.
--
-- Many of the mappings use 'mini.nvim' modules set up in 'plugin/30_mini.lua'.

-- Create a global table with information about Leader groups in certain modes.
-- This is used to provide 'mini.clue' with extra clues.
-- Add an entry if you create a new group.
Config.leader_group_clues = {
  { mode = 'n', keys = '<Leader>b', desc = '+Buffer' },
  { mode = 'n', keys = '<Leader>e', desc = 'Explorer' },
  { mode = 'n', keys = '<Leader>f', desc = '+Find' },
  { mode = 'n', keys = '<Leader>g', desc = '+Git' },
  { mode = 'n', keys = '<Leader>l', desc = '+Language' },
  { mode = 'n', keys = '<Leader>m', desc = '+Map' },
  { mode = 'n', keys = '<Leader>o', desc = '+Other' },
  { mode = 'n', keys = '<Leader>q', desc = '+Quit' },
  { mode = 'n', keys = '<Leader>s', desc = '+Search' },
  -- { mode = 'n', keys = '<Leader>t', desc = '+Terminal' },
  { mode = 'n', keys = '<Leader>v', desc = '+Visits' },
  { mode = 'x', keys = '<Leader>g', desc = '+Git' },
  { mode = 'x', keys = '<Leader>l', desc = '+Language' },
}

-- Helpers for a more concise `<Leader>` mappings.
-- Most of the mappings use `<Cmd>...<CR>` string as a right hand side (RHS) in
-- an attempt to be more concise yet descriptive. See `:h <Cmd>`.
-- This approach also doesn't require the underlying commands/functions to exist
-- during mapping creation: a "lazy loading" approach to improve startup time.
local nmap_leader = function(suffix, rhs, desc)
  vim.keymap.set('n', '<Leader>' .. suffix, rhs, { desc = desc })
end
local xmap_leader = function(suffix, rhs, desc)
  vim.keymap.set('x', '<Leader>' .. suffix, rhs, { desc = desc })
end

-- b is for 'Buffer'. Common usage:
-- - `<Leader>bs` - create scratch (temporary) buffer
-- - `<Leader>ba` - navigate to the alternative buffer
-- - `<Leader>bw` - wipeout (fully delete) current buffer
local new_scratch_buffer = function()
  vim.api.nvim_win_set_buf(0, vim.api.nvim_create_buf(true, true))
end

-- Buffer navigation
nmap('<S-h>', '<Cmd>bprevious<CR>', 'Prev buffer')
nmap('<S-l>', '<Cmd>bnext<CR>',     'Next buffer')
nmap_leader('ba', '<Cmd>b#<CR>',                                'Alternate')
nmap_leader('`', '<Cmd>b#<CR>',                                'Alternate')
nmap_leader('bb', '<Cmd>lua MiniBufremove.delete()<CR>',        'Delete')
-- nmap_leader('bD', '<Cmd>lua MiniBufremove.delete(0, true)<CR>', 'Delete!')
nmap_leader('bs', new_scratch_buffer,                           'Scratch')
nmap_leader('.', '<Cmd>lua Config.open_scratch()<CR>',          'Toggle Scratch Buffer (floating)')
nmap_leader('S', '<Cmd>lua Snacks.scratch.select()<CR>',        'Select Scratch Buffer')
nmap_leader('n', '<Cmd>lua MiniNotify.show_history()<CR>',      'Notification History')
-- nmap_leader('bw', '<Cmd>lua MiniBufremove.wipeout()<CR>',        'Wipeout')
-- nmap_leader('bW', '<Cmd>lua MiniBufremove.wipeout(0, true)<CR>', 'Wipeout!')

nmap_leader('e', '<Cmd>lua Snacks.explorer()<CR>',        'Explorer')
nmap_leader('E', '<Cmd>lua Snacks.explorer.reveal()<CR>', 'Explorer reveal')

-- f is for 'Find'. Common usage:
-- - `<Leader><space>` - find files
-- - `<Leader>fb`     - find open buffers
-- - `<Leader>fv`     - find recent files
local snacks = function(picker, opts)
  return function() require('snacks').picker[picker](opts) end
end

nmap_leader(' ',  snacks('files'),   'Files')
nmap_leader(',',  snacks('buffers'), 'Buffers')
nmap_leader('fb', snacks('buffers'), 'Buffers')
nmap_leader('fv', snacks('recent'),  'Recent (all)')
nmap_leader('fV', snacks('files'),   'Files (cwd)')

-- s is for 'Search'. Common usage:
-- - `<Leader>/`  - live grep
-- - `<Leader>sb` - buffer lines
-- - `<Leader>sd` - diagnostics
-- - `<Leader>sh` - help pages
-- - `<Leader>sR` - resume last picker
nmap_leader('/',  snacks('grep'),                'Grep live')
nmap_leader('sb', snacks('lines'),               'Buffer Lines')
nmap_leader('sB', snacks('grep_buffers'),        'Grep Open Buffers')
nmap_leader('sw', snacks('grep_word'),           'Grep word')
xmap_leader('sw', snacks('grep_word'),           'Grep word')
nmap_leader('s"', snacks('registers'),           'Registers')
nmap_leader('s/', snacks('search_history'),      'Search History')
nmap_leader('sc', snacks('command_history'),     'Command History')
nmap_leader('sC', snacks('commands'),            'Commands')
nmap_leader('sd', snacks('diagnostics'),         'Diagnostics')
nmap_leader('sD', snacks('diagnostics_buffer'),  'Buffer Diagnostics')
nmap_leader('sj', snacks('jumps'),               'Jumps')
nmap_leader('sk', snacks('keymaps'),             'Keymaps')
nmap_leader('sl', snacks('loclist'),             'Location List')
nmap_leader('sm', snacks('marks'),               'Marks')
nmap_leader('sq', snacks('qflist'),              'Quickfix List')
nmap_leader('sr', snacks('resume'),              'Resume')
nmap_leader('ss', snacks('lsp_workspace_symbols'), 'Symbols workspace')
nmap_leader('sS', snacks('lsp_symbols'),           'Symbols document')
nmap_leader('su', snacks('undo'),                'Undotree')

-- g is for 'Git'. Common usage:
-- - `<Leader>gs` - show information at cursor
-- - `<Leader>go` - toggle 'mini.diff' overlay to show in-buffer unstaged changes
-- - `<Leader>gd` - show unstaged changes as a patch in separate tabpage
-- - `<Leader>gL` - show Git log of current file
-- local git_log_cmd = [[Git log --pretty=format:\%h\ \%as\ │\ \%s --topo-order]]
-- local git_log_buf_cmd = git_log_cmd .. ' --follow -- %'
nmap_leader('gg', '<Cmd>lua Config.open_lazygit()<CR>',     'Lazygit')
-- nmap_leader('ga', '<Cmd>Git diff --cached<CR>',             'Added diff')
-- nmap_leader('gA', '<Cmd>Git diff --cached -- %<CR>',        'Added diff buffer')
-- nmap_leader('gc', '<Cmd>Git commit<CR>',                    'Commit')
-- nmap_leader('gC', '<Cmd>Git commit --amend<CR>',            'Commit amend')
-- nmap_leader('gd', '<Cmd>Git diff<CR>',                      'Diff')
-- nmap_leader('gD', '<Cmd>Git diff -- %<CR>',                 'Diff buffer')
-- nmap_leader('gl', '<Cmd>' .. git_log_cmd .. '<CR>',         'Log')
-- nmap_leader('gL', '<Cmd>' .. git_log_buf_cmd .. '<CR>',     'Log buffer')
-- nmap_leader('go', '<Cmd>lua MiniDiff.toggle_overlay()<CR>', 'Toggle overlay')
-- nmap_leader('gs', '<Cmd>lua MiniGit.show_at_cursor()<CR>',  'Show at cursor')
--
-- xmap_leader('gs', '<Cmd>lua MiniGit.show_at_cursor()<CR>', 'Show at selection')

-- l is for 'Language'. Common usage:
-- - `<Leader>ld` - show more diagnostic details in a floating window
-- - `<Leader>lr` - perform rename via LSP
-- - `<Leader>la` - code actions
nmap_leader('la', '<Cmd>lua vim.lsp.buf.code_action()<CR>',   'Actions')
nmap_leader('ld', '<Cmd>lua vim.diagnostic.open_float()<CR>', 'Diagnostic popup')
nmap_leader('lf', '<Cmd>lua require("conform").format()<CR>', 'Format')
nmap_leader('lr', '<Cmd>lua vim.lsp.buf.rename()<CR>',        'Rename')

xmap_leader('lf', '<Cmd>lua require("conform").format()<CR>', 'Format selection')

-- LSP navigation (LazyVim style). Common usage:
-- - `gd` - goto definition
-- - `gr` - references
-- - `gI` - goto implementation
-- - `gy` - goto type definition
-- - `K`  - hover docs
-- - `gK` - signature help

-- Remove Neovim built-in LSP defaults that conflict with our gr mapping
remove_lsp_mapping('n', 'gra')
remove_lsp_mapping('x', 'gra')
remove_lsp_mapping('n', 'gri')
remove_lsp_mapping('n', 'grn')
remove_lsp_mapping('n', 'grr')
remove_lsp_mapping('n', 'grt')
remove_lsp_mapping('n', 'grx')

nmap('gd', '<Cmd>lua vim.lsp.buf.definition()<CR>',      'Goto Definition')
nmap('gr', snacks('lsp_references'),              'References')
nmap('gI', '<Cmd>lua vim.lsp.buf.implementation()<CR>',  'Goto Implementation')
nmap('gy', '<Cmd>lua vim.lsp.buf.type_definition()<CR>', 'Goto T[y]pe Definition')
nmap('K',  '<Cmd>lua vim.lsp.buf.hover()<CR>',           'Hover')
nmap('gK', '<Cmd>lua vim.lsp.buf.signature_help()<CR>',  'Signature Help')

-- Next/prev LSP reference ]] / [[ and <a-n> / <a-p>)
nmap(']]',    function() Snacks.words.jump( 1, true) end, 'Next Reference')
nmap('[[',    function() Snacks.words.jump(-1, true) end, 'Prev Reference')
nmap('<A-n>', function() Snacks.words.jump( 1, true) end, 'Next Reference')
nmap('<A-p>', function() Snacks.words.jump(-1, true) end, 'Prev Reference')

-- m is for 'Map'. Common usage:
-- - `<Leader>mt` - toggle map from 'mini.map' (closed by default)
-- - `<Leader>mf` - focus on the map for fast navigation
-- - `<Leader>ms` - change map's side (if it covers something underneath)
nmap_leader('mf', '<Cmd>lua MiniMap.toggle_focus()<CR>', 'Focus (toggle)')
nmap_leader('mr', '<Cmd>lua MiniMap.refresh()<CR>',      'Refresh')
nmap_leader('ms', '<Cmd>lua MiniMap.toggle_side()<CR>',  'Side (toggle)')
nmap_leader('mt', '<Cmd>lua MiniMap.toggle()<CR>',       'Toggle')

-- q is for 'Quit'
nmap_leader('qq', '<Cmd>quitall<CR>', 'Quit Neovim')

-- o is for 'Other'. Common usage:
-- - `<Leader>oz` - toggle between "zoomed" and regular view of current buffer
nmap_leader('or', '<Cmd>lua MiniMisc.resize_window()<CR>', 'Resize to default width')
nmap_leader('ot', '<Cmd>lua MiniTrailspace.trim()<CR>',    'Trim trailspace')
nmap_leader('oz', '<Cmd>lua Config.toggle_zen()<CR>',      'Zen toggle')

-- t is for 'Terminal'
-- nmap_leader('tT', '<Cmd>horizontal term<CR>', 'Terminal (horizontal)')
-- nmap_leader('tt', '<Cmd>vertical term<CR>',   'Terminal (vertical)')

-- v is for 'Visits'. Common usage:
-- - `<Leader>vv` - add    "core" label to current file.
-- - `<Leader>vV` - remove "core" label to current file.
-- - `<Leader>vc` - pick among all files with "core" label.
local mini_visits_picker = function(label, cwd)
  return function()
    local paths = MiniVisits.list_paths(cwd, { filter = label })
    Snacks.picker.pick({
      title = label and ('Visits: ' .. label) or 'Visit History',
      finder = function()
        return vim.tbl_map(function(path)
          return { file = path, text = path }
        end, paths)
      end,
      format = 'file',
    })
  end
end

nmap_leader('vc', mini_visits_picker('core'),      'Core visits (all)')
nmap_leader('vC', mini_visits_picker('core', '.'), 'Core visits (cwd)')
nmap_leader('vv', '<Cmd>lua MiniVisits.add_label("core")<CR>',    'Add "core" label')
nmap_leader('vV', '<Cmd>lua MiniVisits.remove_label("core")<CR>', 'Remove "core" label')

-- incremental selection treesitter/lsp
vim.keymap.set({ "n", "x", "o" }, "<A-o>", function()
  if vim.treesitter.get_parser(nil, nil, { error = false }) then
    require("vim.treesitter._select").select_parent(vim.v.count1)
  else
    vim.lsp.buf.selection_range(vim.v.count1)
  end
end, { desc = "Select parent treesitter node or outer incremental lsp selections" })

vim.keymap.set({ "n", "x", "o" }, "<A-i>", function()
  if vim.treesitter.get_parser(nil, nil, { error = false }) then
    require("vim.treesitter._select").select_child(vim.v.count1)
  else
    vim.lsp.buf.selection_range(-vim.v.count1)
  end
end, { desc = "Select child treesitter node or inner incremental lsp selections" })

-- stylua: ignore end
