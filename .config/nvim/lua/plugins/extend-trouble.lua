return {
  "folke/trouble.nvim",
  keys = {
    {
      "<leader>xr",
      function()
        require("trouble").open({ mode = require("trouble.sources.fzf").mode() })
      end,
      desc = "Resume Trouble fzf",
    },
  },
}
