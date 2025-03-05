#!/bin/sh

if ! tmux has-session -t '=zig' 2>/dev/null; then
  tmux new-session -d -s zig -n main -c ~/Workspace/zig zsh
  tmux split-window -c ~/Workspace/zig -t 1 -v zsh
  tmux send-keys -t 1 'nvim' C-m
  tmux resize-pane -t 1 -y '80%'
  tmux select-pane -t 1
fi
tmux a -t '=zig'
