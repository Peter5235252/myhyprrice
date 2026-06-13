import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, Gio, GtkLayerShell
import subprocess, json, os, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
from config.live import get as hyprctl_get, set_value as hyprctl_set
from config.writer import write_changes, remove_overrides

GAMEMODE_STATE = BASE / ".gamemode_state.json"

GAMEMODE_KEYS = [
    "decoration.blur.enabled",
    "decoration.dim_inactive",
    "animations.enabled",
    "decoration.rounding",
    "decoration.shadow.enabled",
]

GAMEMODE_VALUES = {
    "decoration.blur.enabled": False,
    "decoration.dim_inactive": False,
    "animations.enabled": False,
    "decoration.rounding": 0,
    "decoration.shadow.enabled": False,
}


def gsettings_get(schema, key):
    return subprocess.run(["gsettings", "get", schema, key], capture_output=True, text=True).stdout.strip()


def gsettings_set(schema, key, value):
    subprocess.run(["gsettings", "set", schema, key, value], capture_output=True)


def hyprctl_val(key: str):
    r = hyprctl_get(key)
    if isinstance(r, dict) and "value" in r:
        return r["value"]
    return None


def bool_val(key: str) -> bool:
    v = hyprctl_val(key)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "yes", "1")
    return bool(v)


def int_val(key: str) -> int:
    v = hyprctl_val(key)
    if isinstance(v, (int, float)):
        return int(v)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


class ToggleRow(Gtk.Box):
    def __init__(self, label, getter, setter):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.setter = setter
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        lbl = Gtk.Label(label=label, xalign=0, hexpand=True)
        self.pack_start(lbl, True, True, 0)

        self.switch = Gtk.Switch()
        self.switch.set_active(self._read(getter))
        self.switch.connect("notify::active", lambda sw, ps: setter(sw.get_active()))
        self.pack_end(self.switch, False, False, 0)

    def _read(self, getter):
        try:
            v = getter()
            if isinstance(v, str):
                return v.lower() in ("true", "yes", "1")
            return bool(v)
        except Exception:
            return False


class ActionButton(Gtk.Box):
    def __init__(self, label, icon_name, command):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        btn = Gtk.Button()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.pack_start(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU), False, False, 0)
        hbox.pack_start(Gtk.Label(label=label), False, False, 0)
        btn.add(hbox)
        btn.set_hexpand(True)
        btn.set_halign(Gtk.Align.FILL)
        btn.set_size_request(-1, 38)
        btn.get_style_context().add_class("sidebar-btn")
        btn.connect("clicked", lambda b: (
            subprocess.Popen(["sh", "-c", command]),
            Gtk.main_quit()
        ))
        self.pack_start(btn, True, True, 0)


def section_label(text):
    lbl = Gtk.Label(label=text, xalign=0)
    lbl.set_margin_start(16)
    lbl.set_margin_top(12)
    lbl.set_margin_bottom(4)
    lbl.get_style_context().add_class("section-label")
    return lbl


def separator():
    s = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    s.set_margin_top(6)
    s.set_margin_bottom(6)
    return s


class HyprSidebar:
    def __init__(self):
        self.win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        self.win.set_title("HyprSidebar")
        self.win.set_default_size(280, 600)
        self.win.set_resizable(False)
        self.win.set_decorated(False)
        self.win.set_keep_above(True)
        self.win.set_skip_taskbar_hint(True)
        self.win.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.win.stick()

        self._setup_layer_shell()
        self._load_css()
        self._build_ui()

        self.win.connect("key-press-event", self._on_key)
        self.win.connect("focus-out-event", lambda w, e: w.destroy())

        GLib.timeout_add_seconds(2, self._poll_gamemode)

    def _setup_layer_shell(self):
        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, 48)
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.BOTTOM, 8)
        GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.RIGHT, 8)
        GtkLayerShell.set_exclusive_zone(self.win, 0)
        GtkLayerShell.auto_exclusive_zone_enable(self.win)

    def _load_css(self):
        css = b"""
            @define-color surface #131318;
            @define-color muted #918f9a;
            @define-color subtle #c7c5d0;
            @define-color text #e4e1e9;
            @define-color rose #444559;
            @define-color highlight-med #2a292f;
            @define-color highlight-high #35343a;

            window {
                background-color: @surface;
                border-radius: 16px;
                border: 1px solid @highlight-med;
            }
            .section-label {
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
                color: @muted;
            }
            button.sidebar-btn {
                background-color: @highlight-med;
                border-radius: 10px;
                border: none;
                box-shadow: none;
                color: @subtle;
                font-size: 13px;
                padding: 6px 12px;
                min-height: 36px;
                text-shadow: none;
            }
            button.sidebar-btn:hover {
                background-color: @highlight-high;
            }
            button.sidebar-btn label {
                color: @subtle;
            }
            switch:checked {
                background-color: @rose;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def _persist(self, key: str, value):
        write_changes({key: value})
        hyprctl_set(key, str(value).lower())

    def _remove_overrides(self, keys: list[str]):
        remove_overrides(keys)

    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        title = Gtk.Label()
        title.set_markup("<b>Quick Settings</b>")
        title.set_margin_start(16)
        title.set_margin_end(16)
        title.set_margin_top(14)
        title.set_margin_bottom(14)
        vbox.pack_start(title, False, False, 0)

        vbox.pack_start(Gtk.Separator(), False, False, 0)

        # Theme
        vbox.pack_start(section_label("THEME"), False, False, 0)
        self.dark_toggle = ToggleRow(
            "Dark Mode",
            lambda: "prefer-dark" in gsettings_get("org.gnome.desktop.interface", "color-scheme"),
            lambda v: gsettings_set("org.gnome.desktop.interface", "color-scheme", "'prefer-dark'" if v else "'default'"),
        )
        vbox.pack_start(self.dark_toggle, False, False, 0)
        vbox.pack_start(separator(), False, False, 0)

        # Hyprland
        vbox.pack_start(section_label("HYPRLAND"), False, False, 0)

        self.blur_toggle = ToggleRow(
            "Blur",
            lambda: bool_val("decoration:blur:enabled"),
            lambda v: self._persist("decoration.blur.enabled", v),
        )
        vbox.pack_start(self.blur_toggle, False, False, 0)

        self.dim_toggle = ToggleRow(
            "Dim Inactive",
            lambda: bool_val("decoration:dim_inactive"),
            lambda v: self._persist("decoration.dim_inactive", v),
        )
        vbox.pack_start(self.dim_toggle, False, False, 0)

        self.anim_toggle = ToggleRow(
            "Animations",
            lambda: bool_val("animations:enabled"),
            lambda v: self._persist("animations.enabled", v),
        )
        vbox.pack_start(self.anim_toggle, False, False, 0)

        self.round_toggle = ToggleRow(
            "Rounding",
            lambda: int_val("decoration:rounding") > 0,
            lambda v: self._persist("decoration.rounding", 12 if v else 0),
        )
        vbox.pack_start(self.round_toggle, False, False, 0)

        vbox.pack_start(separator(), False, False, 0)

        # System
        vbox.pack_start(section_label("SYSTEM"), False, False, 0)
        self.gm_toggle = ToggleRow("Gamemode", self._gamemode_active, self._toggle_gamemode)
        vbox.pack_start(self.gm_toggle, False, False, 0)
        vbox.pack_start(separator(), False, False, 0)

        # Actions
        vbox.pack_start(section_label("ACTIONS"), False, False, 0)
        actions = [
            ("HyprSettings", "preferences-system-symbolic", f"python3 {BASE/'main.py'}"),
            ("Reload Waybar", "view-refresh-symbolic", "killall -SIGUSR2 waybar"),
        ]
        for lbl, icon, cmd in actions:
            vbox.pack_start(ActionButton(lbl, icon, cmd), False, False, 0)
        vbox.pack_start(separator(), False, False, 0)

        # Power
        vbox.pack_start(section_label("POWER"), False, False, 0)
        power = [
            ("Lock", "system-lock-screen-symbolic", "loginctl lock-session"),
            ("Logout", "system-log-out-symbolic", "hyprctl dispatch exit"),
            ("Reboot", "view-refresh-symbolic", "systemctl reboot"),
            ("Shutdown", "system-shutdown-symbolic", "systemctl poweroff"),
        ]
        for lbl, icon, cmd in power:
            vbox.pack_start(ActionButton(lbl, icon, cmd), False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(vbox)
        self.win.add(scrolled)

    def _gamemode_active(self):
        if GAMEMODE_STATE.exists():
            return True
        return False

    def _toggle_gamemode(self, active):
        if active:
            saved = {}
            for key in GAMEMODE_KEYS:
                lua_key = key.replace(".", ":")
                try:
                    val = hyprctl_val(lua_key)
                    if val is not None:
                        saved[key] = val
                except Exception:
                    pass
            GAMEMODE_STATE.write_text(json.dumps(saved))
            write_changes(GAMEMODE_VALUES)
            for key, val in GAMEMODE_VALUES.items():
                lua_key = key.replace(".", ":")
                hyprctl_set(lua_key, str(val).lower())
            self._sync_toggles()
        else:
            if GAMEMODE_STATE.exists():
                saved = json.loads(GAMEMODE_STATE.read_text())
                GAMEMODE_STATE.unlink()
                restore = {}
                for key in GAMEMODE_KEYS:
                    if key in saved and saved[key] is not None:
                        restore[key] = saved[key]
                if restore:
                    write_changes(restore)
                    for key, val in restore.items():
                        lua_key = key.replace(".", ":")
                        hyprctl_set(lua_key, str(val).lower())
                else:
                    remove_overrides(GAMEMODE_KEYS)
            self._sync_toggles()

    def _sync_toggles(self):
        self.blur_toggle.switch.set_active(bool_val("decoration:blur:enabled"))
        self.dim_toggle.switch.set_active(bool_val("decoration:dim_inactive"))
        self.anim_toggle.switch.set_active(bool_val("animations:enabled"))
        self.round_toggle.switch.set_active(int_val("decoration:rounding") > 0)

    def _poll_gamemode(self):
        return True

    def _on_key(self, _w, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q):
            Gtk.main_quit()
            return True
        return False

    def run(self):
        self.win.show_all()
        Gtk.main()


def main():
    app = HyprSidebar()
    app.run()


if __name__ == "__main__":
    main()
