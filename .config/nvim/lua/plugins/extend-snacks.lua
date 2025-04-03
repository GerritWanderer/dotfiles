return {
  "folke/snacks.nvim",
  opts = {
    picker = {
      sources = {
        explorer = {
          hidden = true,
          ignored = true,
          auto_close = false,
          layout = {
            present = "sidebar",
            preview = false,
          },
        },
      },
    },
  },
}
