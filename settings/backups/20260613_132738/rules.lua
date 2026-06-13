hl.layer_rule({
    name = "rofi-slide",
    match = { 
        namespace = "rofi" 
    },
    animation = "fade",
})

hl.window_rule({
    name = "volume-popup-rules",
    match = { 
        title = "VolumePopup" 
    },
    float = true,
    pin = true,
    border_size = 0,
    no_shadow = true,
    stay_focused = true,
    move = { "cursor_x - 30", "cursor_y - 20" },
})

hl.window_rule({
    match  = { class = "xdg-desktop-portal-gtk" },
    float  = true,
    size   = { 800, 500 },
    center = true,
})

hl.window_rule({
    match  = { class = "firefox", title = "Save Image" },
    float  = true,
    size   = { 800, 500 },
    center = true,
})

hl.window_rule({
    match  = { class = "pavucontrol" },
    float  = true,
    size   = { 700, 450 },
    center = true,
})

hl.window_rule({
    match  = { class = "blueman-manager" },
    float  = true,
    size   = { 600, 450 },
    center = true,
})

hl.window_rule({
    match  = { class = "kitty", title = "nmtui" },
    float  = true,
    size   = { 600, 400 },
    center = true,
})

hl.window_rule({
    match  = { class = "nm-connection-editor" },
    float  = true,
    size   = { 700, 500 },
    center = true,
})
