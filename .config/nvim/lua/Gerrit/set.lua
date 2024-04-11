vim.opt.guicursor = ""
vim.opt.nu = true
vim.opt.relativenumber = true

vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true
vim.opt.autoindent = true
vim.opt.wrap = false

vim.opt.scrolloff = 8
vim.opt.cursorline = true

vim.g.mapleader = ' '
vim.g.maplocalleader = ','

-- search related settings
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- nvim tree specific configuration
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
-- optionally enable 24-bit colour
vim.opt.termguicolors = true
-- nvim tree specific configuration end

-- backspace
vim.opt.backspace = 'indent,eol,start'
vim.opt.clipboard:append('unnamedplus')

-- window splits
vim.opt.splitright = true
vim.opt.splitbelow = true
