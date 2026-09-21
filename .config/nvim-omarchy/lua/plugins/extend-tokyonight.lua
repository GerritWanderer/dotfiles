return {
	"folke/tokyonight.nvim",
	config = function()
		require("tokyonight").setup({
			on_highlights = function(hl, c)
				hl.DiagnosticUnnecessary = { fg = c.comment }
			end,
		})
	end,
}
