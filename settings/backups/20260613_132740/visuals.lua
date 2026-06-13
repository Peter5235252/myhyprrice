hl.monitor({
    output   = "eDP-1",
    mode     = "1920x1080@60",
    position = "0x0",
    scale    = 1.2,
})

hl.env("MOZ_ENABLE_WAYLAND",          "1")
hl.env("ELECTRON_OZONE_PLATRAM_HINT","auto")
hl.env("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
hl.env("QT_QPA_PLATFORM",            "wayland;xcb")
hl.env("GDK_BACKEND",                "wayland,x11,*")
hl.env("XCURSOR_SIZE",               "24")

hl.config({
    xwayland = {
        force_zero_scaling = true,
    },

    input = {
        kb_layout    = "hu",
        follow_mouse = 1,

        touchpad = {
            natural_scroll = false,
            tap_to_click   = true,
        },
    },

    general = {
        gaps_in     = 4,
        gaps_out    = 8,
        border_size = 2,

        col = {
            active_border = {
                colors = { active_border_color },
                angle  = 0,
            },
            inactive_border = inactive_border_color,
        },

        layout = DM.current_layout,
    },

    decoration = {
        rounding = 10,
    },

    scrolling = {
        column_width = 0.9,
        fullscreen_on_one_column = true,
    }
})
