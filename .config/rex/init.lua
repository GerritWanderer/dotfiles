-- Shortcuts recorded in Rex, written the way a configuration file spells them.
-- Paste them into your init.lua, then use Reset All in Rex to clear them there.

rex.unbind("shift+cmd+]", "client.tab.next")
rex.unbind("shift+cmd+[", "client.tab.previous")
rex.unbind("alt+cmd+left", "pane.focus.left")
rex.unbind("alt+cmd+right", "pane.focus.right")
rex.unbind("alt+cmd+up", "pane.focus.up")
rex.unbind("alt+cmd+down", "pane.focus.down")

rex.bind("ctrl+h", "pane.focus.left")
rex.bind("ctrl+l", "pane.focus.right")
rex.bind("ctrl+k", "pane.focus.up")
rex.bind("ctrl+j", "pane.focus.down")
rex.bind("alt+n", "client.tab.next")
rex.bind("alt+p", "client.tab.previous")

rex.bind("ctrl+space>c", "client.tab.new")
rex.bind("ctrl+space>shift+x", "client.tab.close")
rex.bind("ctrl+space>r", "client.tab.rename")
rex.bind("ctrl+space>shift+r", "session.rename")
rex.bind("ctrl+space>z", "pane.zoom")
rex.bind("ctrl+space>x", "pane.close")

rex.bind("alt+cmd+e", "session.open_on_web")
-- Shortcuts recorded in Rex, written the way a configuration file spells them.
-- Paste them into your init.lua, then use Reset All in Rex to clear them there.
