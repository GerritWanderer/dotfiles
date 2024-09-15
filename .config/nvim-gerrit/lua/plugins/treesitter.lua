return {
  {"nvim-treesitter/nvim-treesitter", build = ":TSUpdate",
  config = function()
    vim.cmd("set noautoindent")
    vim.cmd("set smartindent")
    vim.cmd("filetype indent off")
    require('nvim-treesitter.configs').setup {
      ensure_installed = { "ruby", "javascript", "typescript", "norg", "c", "lua", "vim", "vimdoc", "query" },
        sync_install = false,
        auto_install = true,

        highlight = {
          enable = true,
          additional_vim_regex_highlighting = false,
        }
      }
    end
  }
}
