-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
--
vim.keymap.set("n", "<C-u>", "<C-u>zz>", { desc = "Scroll half page up centered", remap = true })
vim.keymap.set("n", "<C-d>", "<C-d>zz>", { desc = "Scroll half page down centered", remap = true })
-- swap ctrl+i and ctrl+o for better sanity
