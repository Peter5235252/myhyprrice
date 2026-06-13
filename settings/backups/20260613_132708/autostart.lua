hl.on("hyprland.start", function()
    hl.exec_cmd("pkill dunst || pkill swaync || pkill mako")
    hl.exec_cmd("mako")
    hl.exec_cmd("waybar")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    
    hl.exec_cmd("echo 'Xft.dpi: 115.2' | xrdb -merge")
end)

hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd("systemctl suspend"), { locked = true })

hl.on("monitor.added",   function(m) notify("External display connected",    m.name, "normal",   3000, 991052) end)
hl.on("monitor.removed", function(m) notify("External display disconnected",  m.name, "normal",   3000, 991052) end)

hl.bind("SUPER + SHIFT + P", hl.dsp.exec_cmd("kitty -- pacseek"))
