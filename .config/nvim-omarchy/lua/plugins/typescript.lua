return {
	{
		"neovim/nvim-lspconfig",
		---@type PluginLspOpts
		opts = {
			servers = {
				tsc = {
					settings = {
						["js/ts"] = {
							preferences = {
								importModuleSpecifier = "relative",
								importModuleSpecifierEnding = "minimal",
							},
						},
					},
				},
			},
		},
	},
}
