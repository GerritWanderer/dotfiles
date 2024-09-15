-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
--
vim.keymap.set("i", "jj", "<ESC>", { desc = "exit insert mode with jj" })
vim.keymap.set("n", "<leader>aa", "<cmd>PrtChatToggle<cr>", { desc = "Open AI Chat", remap = true })
vim.keymap.set("n", "<leader>as", "<cmd>PrtChatRespond<cr>", { desc = "Submnit AI Chat", remap = true })
