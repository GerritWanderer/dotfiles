#!/bin/sh

if ! tmux has-session -t '=dtc' 2>/dev/null; then
  tmux new-session -d -s dtc -n main -c ~/Workspace/dtc-platform zsh
  tmux split-window -c ~/Workspace/dtc-platform -t 1 -h zsh
  tmux send-keys -t 1 'nvim' C-m
  tmux send-keys -t 2 'npx ts-node' C-m
  tmux resize-pane -t 1 -x '90%'
  tmux select-pane -t 1
fi
tmux a -t '=dtc'
