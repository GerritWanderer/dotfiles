# Changelog

## 2026-08-25

### Added

- Consistent double-mnemonic sidebar shortcuts for Git, debug, outline, terminal, and collaboration panels

## 2026-08-22

### Added

- Vendor-neutral agent context bindings for the active native or ACP agent
- Enclosing-symbol context with `space a s`
- Agent thread and diff bindings with `space a n` and `space a d`
- LazyVim-style LSP bindings: `gra`, `gri`, `grn`, `grr`, and `grt`
- Buffer navigation with `[b` and `]b`
- First/last and quickfix-style diagnostic navigation
- Git diff, recent-file, buffer-close, centered-layout, and editor-zoom bindings
- Native subword motions matching `nvim-spider`

### Changed

- `space w d` now joins the active pane into the next pane instead of closing its active tab
- Folding now toggles the current fold and fully unfolds with `space z o`
- `space s D` now opens diagnostics for the current file
- Agent and Git panels are configured on the right
- Consolidated duplicate keymap contexts and removed obsolete entries

### Security

- Removed the revoked Context7 API key from active and backup settings
- Kept Context7 enabled for anonymous use without storing credentials in Git
