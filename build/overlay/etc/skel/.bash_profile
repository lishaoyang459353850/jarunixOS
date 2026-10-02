# jarunixOS：在 tty1 自动拉起图形会话
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx /usr/local/bin/jarunix-desktop -- :0 vt1 -nolisten tcp >/tmp/desktop.log 2>&1
fi
