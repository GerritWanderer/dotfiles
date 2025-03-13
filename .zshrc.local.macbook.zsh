eval "$(/Users/gerrit.wanderer/.local/bin/mise activate zsh)"

DISABLE_AUTO_TITLE="true"
function stitle() { echo -en "\e]2;$@\a" }

export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"
export PATH="$(yarn global bin):$PATH"
