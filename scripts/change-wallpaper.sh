#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/wallpaper.jpg"
    exit 1
fi

WP_PATH="$(readlink -f "$1")"

if [ ! -f "$WP_PATH" ]; then
    echo "Error: File does not exist at $WP_PATH"
    exit 1
fi

cat <<EON > /home/csemanpeter/.config/hypr/hyprpaper.conf
splash = false

wallpaper {
    monitor = eDP-1
    path = $WP_PATH
    fit_mode = cover
}
EON

# Restart Wallpaper Engine
pkill hyprpaper
hyprpaper &

# Generate dynamic colors
matugen image "$WP_PATH"

# Reload Services
makoctl reload
killall -SIGUSR2 waybar
pkill -USR1 kitty

# Hot-reload GTK3/GTK4 running instances instantly
CURRENT_THEME=$(gsettings get org.gnome.desktop.interface gtk-theme | tr -d "'")
gsettings set org.gnome.desktop.interface gtk-theme "Default"
gsettings set org.gnome.desktop.interface gtk-theme "$CURRENT_THEME"

# Hot-reload Hyprland Lua borders
hyprctl reload
