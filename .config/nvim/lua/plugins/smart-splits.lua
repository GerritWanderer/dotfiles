return {
  "mrjones2014/smart-splits.nvim",
  build = "./kitty/install-kittens.bash",
  lazy = false,
  keys = {
    {
      "<C-h>",
      function()
        require("smart-splits").move_cursor_left()
      end,
      mode = { "i", "n" },
      desc = "Move to left window",
    },
    {
      "<C-l>",
      function()
        require("smart-splits").move_cursor_right()
      end,
      mode = { "i", "n" },
      desc = "Move to right window",
    },
    {
      "<C-j>",
      function()
        require("smart-splits").move_cursor_down()
      end,
      mode = { "i", "n" },
      desc = "Move to down window",
    },
    {
      "<C-k>",
      function()
        require("smart-splits").move_cursor_up()
      end,
      mode = { "i", "n" },
      desc = "Move to up window",
    },
  },
}