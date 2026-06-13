#!/usr/bin/env bash

# Toggle: If the volume popup is already running, close it and exit
if pgrep -f "VolumePopup" > /dev/null; then
    pkill -f "VolumePopup"
    exit 0
fi

# Get current volume from wireplumber (PipeWire)
CURRENT_VOL=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2 * 100)}')
MUTED_STATE=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -i "MUTED")

# Calculate coordinates directly below the top bar icon
if command -v hyprctl &>/dev/null; then
    read -r x y <<< "$(hyprctl cursorpos | tr -d ',')"
    # Center the slider horizontally with the cursor (slider width is 60px)
    POS_X=$((x - 30))
    # Offset Y below Waybar (10px top margin + 40px height + 5px gap = 55px)
    POS_Y=55
    GEOMETRY="--geometry=60x220+${POS_X}+${POS_Y}"
else
    GEOMETRY="--mouse"
fi

# Run YAD over XWayland so coordinate positioning behaves correctly
GDK_BACKEND=x11 yad --scale \
    --vertical \
    --class="VolumePopup" \
    --name="VolumePopup" \
    --value="$CURRENT_VOL" \
    --print-partial \
    --min-value=0 \
    --max-value=100 \
    --borders=15 \
    --no-buttons \
    --undecorated \
    --close-on-unfocus \
    --skip-taskbar \
    $GEOMETRY \
    --on-top \
    2>/dev/null | while read -r val; do
        wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ "$val%"
        if [ -n "$MUTED_STATE" ]; then
            wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
        fi
done
