# If you come from bash you might have to change your $PATH.
export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH
# add opencode to PATH
export PATH=$HOME/.opencode/bin:$PATH
# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Set name of the theme to load --- if set to "random", it will
# ZSH_THEME="robbyrussell"

# Uncomment the following line if pasting URLs and other text is messed up.
DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to enable command auto-correction.
ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
COMPLETION_WAITING_DOTS="true"

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git z fancy-ctrl-z direnv)

source $ZSH/oh-my-zsh.sh

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# User configuration

# Ignore commands that start with spaces and duplicates.

export HISTCONTROL=ignoreboth

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Don't add certain commands to the history file.

export HISTIGNORE="&:[bf]g:c:clear:history:exit:q:pwd:* --help"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Use custom `less` colors for `man` pages.

export LESS_TERMCAP_md="$(tput bold 2> /dev/null; tput setaf 2 2> /dev/null)"
export LESS_TERMCAP_me="$(tput sgr0 2> /dev/null)"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Make new shells get the history lines from all previous
# shells instead of the default "last window closed" history.

export PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Default editor is neovim
export EDITOR='nvim'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
alias lvim="NVIM_APPNAME=lvim nvim"
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Word deletion: ctrl+w and ctrl+backspace (ghostty sends \x17 for both)
bindkey "^H" backward-delete-word

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if [[ -z "$TMUX" ]] && [[ -n "$SSH_CONNECTION" ]]; then
  tmux new-session -A -s "1) Main"
fi
# Oh my posh setup
eval "$(oh-my-posh init zsh --config ~/.config/oh-my-posh/catppuccin_mocha.omp.json)"
# Activate mise
eval "$(mise activate zsh)"
