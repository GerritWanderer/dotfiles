return {
	"chentoast/marks.nvim",
	config = function()
		require("marks").setup({
			default_mappings = true,
			signs = true,
			mappings = {
				next = "]m",
				prev = "[m",
				delete = "dm",
				delete_buf = "dM",
			},
		})
	end,
}
