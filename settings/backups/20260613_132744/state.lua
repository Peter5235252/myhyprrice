DM = {
    mainMod        = "SUPER",
    rofi_open      = false,
    current_layout = "dwindle",
    is_dragging    = false,
}

function shell_quote(s)
    s = tostring(s or "")
    return "'" .. s:gsub("'", "'\"'\"'") .. "'"
end

function close_rofi()
    hl.exec_cmd("pkill -x rofi || pkill -x rofi-wayland")
    DM.rofi_open = false
end

function launch_rofi_slide()
    hl.layer_rule({
        name = "rofi-slide",
        match = { namespace = "rofi" },
        animation = "slide bottom",
    })
    hl.exec_cmd("rofi -show drun -click-to-exit")
    DM.rofi_open = true
end

function launch_rofi_fade()
    hl.layer_rule({
        name = "rofi-slide",
        match = { namespace = "rofi" },
        animation = "fade",
    })
    hl.exec_cmd("rofi -show drun -click-to-exit")
    DM.rofi_open = true
end

function toggle_rofi()
    if DM.rofi_open then
        close_rofi()
    else
        launch_rofi_fade()
    end
end

local colors_path = os.getenv("HOME") .. "/.config/hypr/colors.lua"
local has_colors, colors = pcall(dofile, colors_path)

active_border_color = "rgba(c4a7e7ff)"
inactive_border_color = "rgba(26233acc)"

if has_colors and colors then
    active_border_color = colors.primary or active_border_color
    inactive_border_color = colors.muted or inactive_border_color
end

function notify(title, body, urgency, timeout, replace_id)
    urgency = urgency or "normal"
    timeout = timeout or 3000

    local cmd = "notify-send -u " .. urgency .. " -t " .. tostring(timeout)
    if replace_id then
        cmd = cmd .. " -h string:x-dunst-stack-tag:" .. tostring(replace_id)
        cmd = cmd .. " -h string:x-canonical-private-synchronous:" .. tostring(replace_id)
    end
    cmd = cmd .. " " .. shell_quote(title) .. " " .. shell_quote(body)
    hl.exec_cmd(cmd)
end

function send_notif(urgency, title, body)
    local cmd    = "notify-send -u " .. urgency .. " -t 0 -p " .. shell_quote(title) .. " " .. shell_quote(body)
    local handle = io.popen(cmd)
    local id     = nil
    if handle then
        id = handle:read("*l")
        handle:close()
    end
    return id
end

function dismiss_notif(id)
    if id then
        hl.exec_cmd("makoctl dismiss -n " .. tostring(id))
    end
end

hl.layout.register("columns", {
    recalculate = function(ctx)
        local n = #ctx.targets
        if n == 0 then return end
        for i, target in ipairs(ctx.targets) do
            target:place(ctx:column(i, n))
        end
    end,
})
