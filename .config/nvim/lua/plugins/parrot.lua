return {
  "frankroeder/parrot.nvim",
  dependencies = { "ibhagwan/fzf-lua", "nvim-lua/plenary.nvim" },
  opts = {},
  config = function()
    require("parrot").setup({
      providers = {
        openai = {
          api_key = os.getenv("OPENAI_API_KEY"),
        },
      },
      toggle_target = "tabnew",
    })
  end,
}
