bindkey "^H" backward-delete-word
export PATH=$PATH:/home/gerrit/.local/bin
if [ -e /home/gerrit/.nix-profile/etc/profile.d/nix.sh ]; then . /home/gerrit/.nix-profile/etc/profile.d/nix.sh; fi # added by Nix installer
