-- Dummy stand-in for the theme spec Omarchy's Linux theme switcher normally
-- generates at this path. Nothing creates it on macOS, so it's provided here
-- by hand (gitignored, machine-local) to keep lua/plugins/theme.lua's
-- symlink -- tracked in the dotfiles repo, unmodified -- resolving instead
-- of erroring on startup. Swap "tokyonight" for whichever installed theme
-- you prefer.
return {
	{ "LazyVim/LazyVim", opts = { colorscheme = "tokyonight" } },
}
