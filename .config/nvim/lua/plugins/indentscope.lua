return {
  "echasnovski/mini.indentscope",
  version = false,
  opts = {
    symbol = "│"
  },
  config = function(_, opts)
    require("mini.indentscope").setup(opts)
  end
}
