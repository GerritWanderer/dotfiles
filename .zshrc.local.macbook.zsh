export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

DISABLE_AUTO_TITLE="true"
function stitle() { echo -en "\e]2;$@\a" }

export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"
export PATH="$(yarn global bin):$PATH"
