case $- in
    *i*) ;;
    *) return ;;
esac
export PATH="$HOME/.local/bin:$PATH"
if [[ -t 0 && -t 1 && ${TERM:-dumb} != dumb && -z ${BLE_VERSION:-} && -r "$HOME/.local/share/blesh/ble.sh" ]]; then
    source "$HOME/.local/share/blesh/ble.sh" --attach=none --rcfile "$HOME/.config/blesh/init.sh"
fi
if [[ -n ${KITTY_WINDOW_ID:-} ]]; then
    if [[ -z ${CLAVIS_TERMINAL_WELCOME_SHOWN:-} ]] && command -v neofetch >/dev/null; then
        export CLAVIS_TERMINAL_WELCOME_SHOWN=1
        neofetch --config "$HOME/.config/neofetch/clavis.conf"
    fi
    if [[ -x "$HOME/.local/bin/starship" ]]; then
        eval "$("$HOME/.local/bin/starship" init bash)"
    fi
fi
if [[ -n ${BLE_VERSION:-} && -t 0 && -t 1 ]]; then
    ble-attach
fi
