# myhyprrice

A personal Hyprland rice for the ThinkPad T480, built on the **Rosé Pine** color scheme. Written entirely in **Lua** (Hyprland 0.55+).

> No hyprlang. No shell-script spaghetti. Just clean, modular Lua config.

---

## Screenshots

*Add a screenshot here once you have one -- drag it into the GitHub repo editor or use `git add`.*

---

## Stack

| Role | Tool |
|---|---|
| Compositor | [Hyprland](https://hyprland.org/) 0.55+ |
| Bar | [Waybar](https://github.com/Alexays/Waybar) |
| Terminal | [Kitty](https://sw.kovidgoyal.net/kitty/) |
| Launcher | [Rofi](https://github.com/davatorium/rofi) |
| Notifications | [Mako](https://github.com/emersion/mako) |
| File Manager | [Dolphin](https://apps.kde.org/dolphin/) |
| Wallpaper | [Hyprpaper](https://github.com/hyprwm/hyprpaper) |
| Color Scheme | [Rosé Pine](https://rosepinetheme.com/) |

---

## Features

- **Dynamic border colors** -- active/inactive borders are pulled from `colors.lua`, defaulting to Rosé Pine Iris and Overlay if no override is set
- **Dual layout toggle** -- switch between standard Dwindle tiling and Hyprland's infinite-tape Scrolling layout on the fly with `SUPER + SHIFT + T`
- **Gesture support** -- 3-finger swipe left/right cycles workspaces, swipe up opens Rofi (slide animation), swipe down closes it
- **Rofi with transitions** -- fade on keyboard shortcut, slide-from-bottom on trackpad gesture
- **Smart notifications** -- volume, brightness, mic, and Bluetooth all send stacking Mako notifications with progress values (no duplicate popups)
- **Lid switch suspend** -- closing the lid suspends the machine, works on the lock screen
- **XWayland scaling fix** -- DPI injected at startup so X11 apps render sharp at 1.2x fractional scale
- **Modular config** -- keybinds, visuals, colors, rules, autostart, and state are all in separate files

---

## File Structure

```
~/.config/hypr/
├── hyprland.lua      # Main entry point
├── keybinds.lua      # All keybindings
├── visuals.lua       # Animations, decorations, blur
├── colors.lua        # Rosé Pine color definitions
├── rules.lua         # Window and layer rules
├── autostart.lua     # Startup applications
├── state.lua         # Shared state (layout, drag, etc.)
├── custom.lua        # Personal overrides
├── hyprpaper.conf    # Wallpaper config
├── scripts/          # Shell scripts
└── settings/         # Settings panel and sidebar
```

---

## Keybinds

### General

| Keybind | Action |
|---|---|
| `SUPER + Return` | Open Kitty terminal |
| `SUPER + Q` | Close focused window |
| `SUPER + V` | Toggle floating window |
| `SUPER + Space` | Toggle Rofi launcher |
| `SUPER + F` | Toggle fullscreen |
| `SUPER + F11` | Toggle maximized |

### Workspaces

| Keybind | Action |
|---|---|
| `SUPER + 1-5` | Switch to workspace |
| `SUPER + SHIFT + 1-5` | Move window to workspace |

### Layout

| Keybind | Action |
|---|---|
| `SUPER + SHIFT + T` | Toggle Dwindle / Scrolling layout |

### Audio

| Keybind | Action |
|---|---|
| `SUPER + F1` | Toggle mute |
| `SUPER + F2` | Volume down 5% |
| `SUPER + F3` | Volume up 5% |
| `SUPER + F4` | Toggle microphone mute |

### Brightness

| Keybind | Action |
|---|---|
| `SUPER + F5` | Brightness down 5% |
| `SUPER + F6` | Brightness up 5% |

### Other

| Keybind | Action |
|---|---|
| `SUPER + F10` | Toggle Bluetooth |
| `SUPER + Equal` | Zoom in (2x) |
| `SUPER + Minus` | Zoom out |
| `Print` | Screenshot (full screen) |
| `SHIFT + Print` | Screenshot (select area) |
| `SUPER + SHIFT + P` | Open pacseek (package manager TUI) |

### Mouse

| Keybind | Action |
|---|---|
| `SUPER + LMB drag` | Move window |
| `SUPER + RMB drag` | Resize window |

---

## Installation

> This config is built for my specific setup (ThinkPad T480, CachyOS, 1080p display at 1.2x scale, Hungarian keyboard layout). You'll need to adjust a few things for your machine.

### Prerequisites

Make sure these are installed before you start:

- Hyprland 0.55 or newer
- Waybar
- Kitty
- Rofi
- Mako
- Hyprpaper
- Dolphin
- brightnessctl
- grimblast
- wireplumber (`wpctl`)
- pacseek (optional)

On Arch / CachyOS:

```bash
sudo pacman -S hyprland waybar kitty rofi mako hyprpaper dolphin brightnessctl wireplumber
yay -S grimblast-git pacseek
```

### Steps

1. **Back up your existing config** if you have one:

```bash
cp -r ~/.config/hypr ~/.config/hypr.bak
```

2. **Clone the repo:**

```bash
git clone https://github.com/Peter5235252/myhyprrice.git
```

3. **Copy the config files:**

```bash
cp -r myhyprrice/* ~/.config/hypr/
```

4. **Adjust for your setup** -- open `hyprland.lua` and change these to match your system:

- `output = "eDP-1"` -- run `hyprctl monitors` to find your display name
- `scale = 1.2` -- adjust for your screen size and preference
- `kb_layout = "hu"` -- change to your keyboard layout (e.g. `"us"`)

5. **Restart Hyprland.** The config hot-reloads the moment you save any `.lua` file, so changes take effect instantly once you're running.

---

## Notes

- The config uses `pcall(require, "settings.overrides")` at the end of `hyprland.lua` -- this silently loads a local overrides file if it exists, so you can make personal tweaks without modifying the main config.
- Border colors are dynamically loaded from `colors.lua`. Edit that file to change the accent colors without touching anything else.
- Mako is explicitly started after killing Dunst and SwayNC to prevent DBus conflicts. If you use a different notification daemon, edit the autostart section in `hyprland.lua`.

---

## License

MIT -- do whatever you want with it.
