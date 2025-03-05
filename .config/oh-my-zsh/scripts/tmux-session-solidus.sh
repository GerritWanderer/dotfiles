#!/bin/sh

if ! tmux has-session -t '=solidus' 2>/dev/null; then
  tmux new-session -d -s solidus -n main -c ~/Workspace/solidus zsh
  tmux split-window -c ~/Workspace/solidus -t 1 -h zsh
  tmux split-window -c ~/Workspace/solidus -t 2 -v zsh
  tmux send-keys -t 1 'nvim' C-m
  tmux send-keys -t 2 'gulp' C-m
  tmux send-keys -t 3 'rails c' C-m
  tmux resize-pane -t 1 -x '80%'
  tmux select-pane -t 1
fi
tmux a -t '=solidus'
