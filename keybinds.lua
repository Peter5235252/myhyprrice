hl.bind(DM.mainMod .. " + Return", hl.dsp.exec_cmd("kitty"))
hl.bind(DM.mainMod .. " + Q", hl.dsp.window.close())
hl.bind(DM.mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))

hl.bind(DM.mainMod .. " + mouse:272", function()
    DM.is_dragging = true
    hl.dispatch(hl.dsp.window.drag())
end, { mouse = true })

hl.bind(DM.mainMod .. " + mouse:272", function()
    DM.is_dragging = false
end, { mouse = true, release = true })

hl.bind(DM.mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

local function toggle_scrolling_layout()
    hl.gesture({ fingers = 3, direction = "horizontal", action = "unset" })

    if DM.current_layout == "dwindle" then
        DM.current_layout = "scrolling"
        hl.config({ general = { layout = "scrolling" } })
        hl.gesture({ fingers = 3, direction = "horizontal", action = "scroll_move" })
        notify("Layout Switched", "Switched to infinite-tape scrolling layout", "normal", 1500, "layout_switch")
    else
        DM.current_layout = "dwindle"
        hl.config({ general = { layout = "dwindle" } })
        hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
        notify("Layout Switched", "Switched to standard dwindle layout", "normal", 1500, "layout_switch")
    end
end

hl.bind("SUPER + SHIFT + T", toggle_scrolling_layout)
hl.bind("SUPER + SHIFT + V", toggle_scrolling_layout)

hl.bind(DM.mainMod .. " + F11", hl.dsp.window.fullscreen({ mode = "maximized", action = "toggle" }))
hl.bind(DM.mainMod .. " + F",   hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))

hl.bind(DM.mainMod .. " + F1", hl.dsp.exec_cmd([[sh -c '
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
    if wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -q MUTED; then
        notify-send -h string:x-dunst-stack-tag:volume -h string:x-canonical-private-synchronous:volume -a volume -c volume -t 1500 "Audio muted" "System audio has been muted"
    else
        vol=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '\''{printf("%.0f", $2 * 100)}'\'')
        notify-send -h string:x-dunst-stack-tag:volume -h string:x-canonical-private-synchronous:volume -a volume -c volume -t 1500 -h int:value:"$vol" "Audio unmuted" "Current volume: ${vol}%"
    fi
']]))

hl.bind(DM.mainMod .. " + F2", hl.dsp.exec_cmd([[sh -c '
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
    vol=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '\''{printf("%.0f", $2 * 100)}'\'')
    notify-send -h string:x-dunst-stack-tag:volume -h string:x-canonical-private-synchronous:volume -a volume -c volume -t 1500 -h int:value:"$vol" "Volume decreased" "Current volume: ${vol}%"
']]))

hl.bind(DM.mainMod .. " + F3", hl.dsp.exec_cmd([[sh -c '
    wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+
    vol=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '\''{printf("%.0f", $2 * 100)}'\'')
    notify-send -h string:x-dunst-stack-tag:volume -h string:x-canonical-private-synchronous:volume -a volume -c volume -t 1500 -h int:value:"$vol" "Volume increased" "Current volume: ${vol}%"
']]))

hl.bind(DM.mainMod .. " + F10", hl.dsp.exec_cmd([[sh -c '
    rfkill toggle bluetooth
    sleep 0.1
    if rfkill list bluetooth | grep -q "Soft blocked: yes"; then
        notify-send -h string:x-dunst-stack-tag:bluetooth -h string:x-canonical-private-synchronous:bluetooth -a bluetooth -c bluetooth -t 1500 "Bluetooth" "Disabled"
    else
        notify-send -h string:x-dunst-stack-tag:bluetooth -h string:x-canonical-private-synchronous:bluetooth -a bluetooth -c bluetooth -t 1500 "Bluetooth" "Enabled"
    fi
']]))

hl.bind("SUPER + Space", function()
    toggle_rofi()
end)

hl.bind("Print",        hl.dsp.exec_cmd("grimblast --freeze copy screen && notify-send 'Screenshot' 'Saved'"), { auto_consuming = true })
hl.bind("SHIFT + Print", hl.dsp.exec_cmd("grimblast --freeze copy area && notify-send 'Screenshot' 'Saved'"), { auto_consuming = true })

hl.bind(DM.mainMod .. " + Equal", function()
    hl.config({ cursor = { zoom_factor = 2.0 } })
end)

hl.bind(DM.mainMod .. " + Minus", function()
    hl.config({ cursor = { zoom_factor = 1.0 } })
end)

for i = 1, 5 do
    hl.bind(DM.mainMod .. " + " .. i, function()
        if DM.is_dragging then
            hl.dispatch(hl.dsp.window.move({ workspace = i }))
        else
            hl.dispatch(hl.dsp.focus({ workspace = i }))
        end
    end)

    hl.bind(DM.mainMod .. " + SHIFT + " .. i, hl.dsp.window.move({ workspace = i }))
end

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

hl.gesture({
    fingers   = 3,
    direction = "up",
    action    = function()
        if not DM.rofi_open then launch_rofi_slide() end
    end,
})

hl.gesture({
    fingers   = 3,
    direction = "down",
    action    = function()
        if DM.rofi_open then close_rofi() end
    end,
})

hl.bind("SUPER + F6", hl.dsp.exec_cmd([[sh -c '
    brightnessctl set 5%+
    pct=$(brightnessctl -m | cut -d, -f4 | tr -d "%")
    notify-send -h string:x-dunst-stack-tag:brightness -h string:x-canonical-private-synchronous:brightness -a brightness -c brightness -t 1500 -h int:value:"$pct" "Brightness increased" "Current brightness: ${pct}%"
']]), {
    repeating = true,
    locked = true
})

hl.bind("SUPER + F5", hl.dsp.exec_cmd([[sh -c '
    brightnessctl set 5%-
    pct=$(brightnessctl -m | cut -d, -f4 | tr -d "%")
    notify-send -h string:x-dunst-stack-tag:brightness -h string:x-canonical-private-synchronous:brightness -a brightness -c brightness -t 1500 -h int:value:"$pct" "Brightness decreased" "Current brightness: ${pct}%"
']]), {
    repeating = true,
    locked = true
})

hl.bind("SUPER + F4", hl.dsp.exec_cmd([[sh -c '
    wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
    sleep 0.05
    if wpctl get-volume @DEFAULT_AUDIO_SOURCE@ | grep -qi "MUTED"; then
        notify-send -h string:x-dunst-stack-tag:mic -h string:x-canonical-private-synchronous:mic -a mic -c mic -t 1500 "Microphone muted" "Input is now disabled"
    else
        notify-send -h string:x-dunst-stack-tag:mic -h string:x-canonical-private-synchronous:mic -a mic -c mic -t 1500 "Microphone active" "Input is now enabled"
    fi
']]))

hl.bind("SUPER + CTRL + S", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/settings/sidebar.sh"))
hl.bind("SUPER + SHIFT + S", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/settings/main.py"))
