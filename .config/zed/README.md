# Zed Configuration

Personal [Zed](https://zed.dev/) configuration focused on LazyVim-compatible muscle memory and agent workflows.

Inspired by [Jellydn's Zed 101 Setup](https://github.com/jellydn/zed-101-setup).

## Highlights

- Vim mode with relative line numbers, smart-case find, yank highlighting, and system clipboard integration
- Gruvbox Dark Hard with Berkeley Mono Variable
- LazyVim-style navigation, diagnostics, Git, folding, buffers, panes, and LSP bindings
- Native and ACP agents, including OpenCode and Codex
- TypeScript through `tsgo`; Python through Pyright and Ruff
- Context7 MCP support without a committed API key

## Keybindings

`space` is the leader key.

### Navigation and panes

| Binding | Action |
| --- | --- |
| `Ctrl-h/j/k/l` | Move between panes |
| `Shift-h/l`, `[b`/`]b` | Previous/next buffer |
| `space ,`, `space space` | Open buffer switcher |
| `space \|`, `space w \|` | Split right |
| `space _`, `space w -` | Split down |
| `space w w` | Activate next pane |
| `space w d` | Close pane by joining it into the next pane |
| `space e` | Reveal current file in project panel |
| `Ctrl-\\` | Toggle terminal |

### Sidebars

| Binding | Panel |
| --- | --- |
| `space a a` | Agent |
| `space g g` | Git |
| `space d d` | Debug |
| `space o o` | Outline |
| `space t t` | Terminal |
| `space c c` | Collaboration |

### Files and search

| Binding | Action |
| --- | --- |
| `space f f`, `space s f` | Find files |
| `space f r`, `space f R` | Find recent files |
| `space f p` | Open recent project |
| `space /`, `space s g` | Project search |
| `space s b` | Search current buffer |
| `space s s` | Document outline |
| `space s S` | Project symbols |

### LSP and diagnostics

| Binding | Action |
| --- | --- |
| `gd`, `gD` | Definition / definition in split |
| `gri` | Implementation |
| `grn` | Rename |
| `grr` | References |
| `grt` | Type definition |
| `gra`, `space c a`, `space .` | Code actions |
| `]d`/`[d` | Next/previous diagnostic |
| `]D`/`[D` | Last/first diagnostic |
| `]q`/`[q` | Diagnostic navigation using LazyVim quickfix muscle memory |
| `space s d` | Project diagnostics |
| `space s D` | Current-file diagnostics |

### Git and folding

| Binding | Action |
| --- | --- |
| `space g g`, `space g s` | Toggle Git panel |
| `space g d`, `space g v` | Working-tree diff |
| `space g D`, `space g V` | Branch diff |
| `]h`/`[h` | Next/previous hunk |
| `space z a` | Toggle fold |
| `space z o` | Unfold all |
| `space z c` | Fold all |

### Agents

These bindings target the active Zed-native or ACP agent rather than a specific vendor.

| Binding | Action |
| --- | --- |
| `space a a` | Toggle agent panel |
| `space a n` | New agent thread |
| `space a d` | Review agent diff |
| `space a s` | Add the enclosing symbol to the active thread |
| `space y`, `space Y` | Add the current line or selection to the active thread |
| `space a y`, `space a Y` | Agent-prefixed aliases for adding context |

`space y` is the Zed equivalent of the Neovim `yank-for-claude` workflow, but works with any active agent and sends structured file/range context directly.

### Vim behavior

- `kj` and `jk` leave insert mode.
- `s` and `S` provide forward/backward sneak motions.
- `w`, `b`, `e`, and `ge` use native subword motions to match `nvim-spider`.
- `space u z` toggles centered layout; `space u Z` toggles editor zoom.

## Installation

```bash
git clone https://github.com/makyinmars/zed-config ~/.config/zed
```

Zed reloads `settings.json` and `keymap.json` automatically.

## Secrets

Do not commit API keys to this repository. Context7 works anonymously with lower rate limits; configure and rotate authenticated keys through the provider dashboard when needed.

## Files

- `settings.json` — editor, language, agent, and MCP configuration
- `keymap.json` — Vim/LazyVim-compatible bindings
- `CHANGELOG.md` — notable configuration changes
