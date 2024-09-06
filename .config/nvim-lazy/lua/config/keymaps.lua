-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
--
vim.keymap.set("i", "jj", "<ESC>", { desc = "exit insert mode with jj" })

-- Move multiple lines
vim.keymap.set("v", "<A-j>", ":m '>+1<CR>gv=gv", {})
vim.keymap.set("v", "<A-k>", ":m '<-2<CR>gv=gv", {})
