-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
local opt = vim.opt
opt.clipboard = "unnamedplus"
opt.relativenumber = false

-- LazyVim root dir detection
-- Each entry can be:
-- * the name of a detector function like `lsp` or `cwd`
-- * a pattern or array of patterns like `.git` or `lua`.
-- * a function with signature `function(buf) -> string|string[]`
vim.g.root_spec = { { ".git", "lua" }, "cwd", "lsp" }
-- vim.g.lazyvim_ruby_lsp = "ruby_lsp"
-- vim.g.lazyvim_ruby_formatter = "rubocop"

-- To disable **all animations**, add the following to your `options.lua`:
vim.g.snacks_animate = false
