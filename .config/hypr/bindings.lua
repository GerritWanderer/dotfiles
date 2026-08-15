-- Keep only your personal keybinding overrides here. Add new bindings or
-- unbind defaults before replacing them.

-- See current bindings and descriptions:
--   omarchy menu keybindings --print

-- To disable every Omarchy default binding, set this in
-- ~/.config/hypr/hyprland.lua before require("default.hypr.omarchy"), then add
-- only the bindings you want below:
--   omarchy_default_bindings = false

-- To disable all preinstalled app/webapp bindings, set:
--   omarchy_preinstalled_bindings = false

-- Add a new binding.
-- o.bind("SUPER + SHIFT + R", "SSH", "alacritty -e ssh your-server")

-- Change an existing binding by unbinding it first, then binding the key again.
-- This example changes SUPER+SPACE from the launcher to the Omarchy root menu.
-- hl.unbind("SUPER + SPACE")
-- o.bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu toggle root")

-- Disable a default binding without replacing it.
-- hl.unbind("SUPER + SHIFT + B")

-- Logitech MX Keys examples:
-- o.bind("SUPER + SHIFT + S", nil, "omarchy-capture-screenshot")
-- o.bind("SUPER + H", nil, "voxtype record toggle")
-- o.bind("SUPER + PERIOD", nil, "omarchy-shell shell toggle omarchy.emojis")

-- DeckShift — reclaim SUPER+SHIFT+S from the Omarchy default, bind Gaming Mode
-- hl.unbind("SUPER + SHIFT + S")
-- o.bind("SUPER + SHIFT + S", "Gaming Mode", "/usr/local/bin/switch-to-gaming")

-- DeckShift — toggle the Gaming Mode control panel
-- o.bind("SUPER + ALT + G", "Gaming Mode panel", "omarchy-shell shell toggle nosignal.deckshift")

-- Close Window
hl.unbind("SUPER + W")
o.bind("SUPER + Q", "Close Window", hl.dsp.window.close())

-- Window Navigation
hl.unbind("SUPER + H")
hl.unbind("SUPER + J")
hl.unbind("SUPER + K")
hl.unbind("SUPER + L")
o.bind("SUPER + H", "Focus Left Window", hl.dsp.focus({ direction = "l" }))
o.bind("SUPER + J", "Focus Bottom Window", hl.dsp.focus({ direction = "d" }))
o.bind("SUPER + K", "Focus Top Window", hl.dsp.focus({ direction = "u" }))
o.bind("SUPER + L", "Focus Right Window", hl.dsp.focus({ direction = "r" }))

-- Swap Windows
hl.unbind("SUPER + SHIFT + H")
hl.unbind("SUPER + SHIFT + J")
hl.unbind("SUPER + SHIFT + K")
hl.unbind("SUPER + SHIFT + L")
o.bind("SUPER + SHIFT + H", "Swap Left Window", hl.dsp.window.swap({ direction = "l" }))
o.bind("SUPER + SHIFT + J", "Swap Bottom Window", hl.dsp.window.swap({ direction = "d" }))
o.bind("SUPER + SHIFT + K", "Swap Top Window", hl.dsp.window.swap({ direction = "u" }))
o.bind("SUPER + SHIFT + L", "Swap Right Window", hl.dsp.window.swap({ direction = "r" }))

-- Scratchpad
hl.unbind("SUPER + S")
hl.unbind("SUPER + ALT + S")
o.bind("SUPER + PERIOD", "Open Scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
o.bind("SUPER + SHIFT + PERIOD", "Move Window to Scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }))

