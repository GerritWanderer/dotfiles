-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
vim.keymap.set('n', '<C-h>', require('smart-splits').move_cursor_left)
vim.keymap.set('n', '<C-j>', require('smart-splits').move_cursor_down)
vim.keymap.set('n', '<C-k>', require('smart-splits').move_cursor_up)
vim.keymap.set('n', '<C-l>', require('smart-splits').move_cursor_right)

-- Marks & jumps (default Neovim behavior, described here so Keycade LazyVim
-- can surface them as trainable cards)
vim.keymap.set("n", "m", "m", { desc = "Set mark" })
vim.keymap.set("n", "`", "`", { desc = "Jump to mark (exact position)" })
vim.keymap.set("n", "'", "'", { desc = "Jump to mark (start of line)" })
vim.keymap.set("n", "``", "``", { desc = "Jump to last position (exact)" })
vim.keymap.set("n", "''", "''", { desc = "Jump to last position (line)" })
vim.keymap.set("n", "`.", "`.", { desc = "Jump to last change" })
vim.keymap.set("n", "`^", "`^", { desc = "Jump to last insert" })
vim.keymap.set("n", "`[", "`[", { desc = "Jump to start of last yank/change" })
vim.keymap.set("n", "`]", "`]", { desc = "Jump to end of last yank/change" })
vim.keymap.set("n", "<C-o>", "<C-o>", { desc = "Jump back in jumplist" })
vim.keymap.set("n", "<C-i>", "<C-i>", { desc = "Jump forward in jumplist" })
