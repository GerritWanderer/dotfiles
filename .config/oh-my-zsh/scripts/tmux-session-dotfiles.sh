#!/bin/sh

if ! tmux has-session -t '=dotfiles' 2>/dev/null; then
  tmux new-session -d -s dotfiles -n main -c ~/dotfiles zsh
  tmux send-keys -t 1 'nvim' C-m
fi
tmux a -t '=dotfiles'
