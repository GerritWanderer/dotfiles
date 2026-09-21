return {
	"nvim-neo-tree/neo-tree.nvim",
	opts = {
		window = {
			mappings = {
				["s"] = false,
				["<cr>"] = function(state)
					-- Open the file
					require("neo-tree.sources.filesystem.commands").open(state)
					-- Close neo-tree
					require("neo-tree.command").execute({ action = "close" })
				end,
			},
		},
		buffers = {
			follow_current_file = {
				enabled = true, -- This will find and focus the file in the active buffer every time
				leave_dirs_open = true, -- `false` closes auto expanded dirs, such as with `:Neotree reveal`
			},
		},
		filesystem = {
			filtered_items = {
				visible = true,
				show_hidden_count = true,
				hide_dotfiles = false,
				hide_gitignored = true,
				hide_by_name = { "node_modules", "git" },
				never_show = { ".git" },
			},
			follow_current_file = {
				enabled = true, -- This will find and focus the file in the active buffer every time
				leave_dirs_open = true, -- `false` closes auto expanded dirs, such as with `:Neotree reveal`
			},
		},
	},
}
