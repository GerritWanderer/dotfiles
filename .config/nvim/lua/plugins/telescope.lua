return {
  {
    'nvim-telescope/telescope.nvim', tag = '0.1.6',
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope-live-grep-args.nvim' },
    config = function()
      local telescope = require('telescope')
      local builtin = require('telescope.builtin')
      local actions = require("telescope.actions")
      -- Clone the default Telescope configuration
      local telescopeConfig = require("telescope.config")
      local vimgrep_arguments = { unpack(telescopeConfig.values.vimgrep_arguments) }

      vim.keymap.set('n', '<leader>ff', builtin.find_files, {})
      vim.keymap.set(
        "n",
        "<leader>fg",
        "<cmd>lua require('telescope').extensions.live_grep_args.live_grep_args()<CR>",
        { desc = "Live Grep" }
      )
      vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<leader>fs', builtin.lsp_document_symbols, {})

      telescope.setup({
        defaults = {
          vimgrep_arguments = vimgrep_arguments,
          path_display = { "truncate" },
          mappings = {
            i = {
              ["<C-j>"] = actions.cycle_history_next,
              ["<C-k>"] = actions.cycle_history_prev,
            },
          },
        },
      })

      require("telescope").load_extension("live_grep_args")
      require("telescope").load_extension("fzf")
    end
  },
  { 'nvim-telescope/telescope-fzf-native.nvim', build = 'make' }
}
