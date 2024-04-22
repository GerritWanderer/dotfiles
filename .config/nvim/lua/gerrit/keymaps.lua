-- Used for default file manager
-- vim.keymap.set('n', '<leader>pv', vim.cmd.Ex)

-- nvim tree
vim.keymap.set('n', '<leader>e', ':NvimTreeToggle<cr>', opts)
vim.keymap.set('i', 'jk', '<ESC>', { desc = 'exit insert mode with jk' })

-- window management
vim.keymap.set("n", "<leader>sv", "<C-w>v", { desc = "Split window vertically" }) -- split window vertically
vim.keymap.set("n", "<leader>sh", "<C-w>s", { desc = "Split window horizontally" }) -- split window horizontally
vim.keymap.set("n", "<leader>se", "<C-w>=", { desc = "Make splits equal size" }) -- make split windows equal width & height
vim.keymap.set("n", "<leader>sx", "<cmd>close<CR>", { desc = "Close current split" }) -- close current split window

-- Telescoope
vim.keymap.set('n', '<leader>q', ':bd<cr>', opts) 

-- Move Lines command

vim.keymap.set('v', '<A-j>', ":m '>+1<CR>gv=gv", opts)
vim.keymap.set('v', '<A-k>', ":m '<-2<CR>gv=gv", opts)
