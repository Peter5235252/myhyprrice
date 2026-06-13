import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio

import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.reader import read_all_configs
from config.live import get, set_value, get_monitors
from config.writer import write_settings, write_monitors, write_env
from config.backup import create as create_backup, list_backups, restore as restore_backup

SCHEMA_PATH = Path(__file__).parent.parent / "schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


class SettingsPage(Gtk.ScrolledWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.changes = {}

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.box.set_margin_start(24)
        self.box.set_margin_end(24)
        self.box.set_margin_top(24)
        self.box.set_margin_bottom(24)

        self.clamp = Adw.Clamp()
        self.list = Gtk.ListBox(css_classes=["boxed-list"])
        self.clamp.set_child(self.list)
        self.box.append(self.clamp)
        self.set_child(self.box)

    def add_row(self, row):
        self.list.append(row)

    def track_change(self, key, value):
        self.changes[key] = value
        set_value(key, value)


class GeneralPage(SettingsPage):
    def __init__(self, settings: dict, schema: dict):
        super().__init__()
        self.settings = settings
        self.schema = schema
        self._build()

    def _build(self):
        keys = [
            ("general.gaps_in", "Gaps In", "Inner window gaps"),
            ("general.gaps_out", "Gaps Out", "Outer window gaps"),
            ("general.border_size", "Border Size", "Width of window borders"),
            ("general.layout", "Layout", "Tiling layout (dwindle/master/scrolling)"),
            ("general.allow_tearing", "Allow Tearing", "Allow screen tearing"),
            ("general.resize_on_border", "Resize on Border", "Resize windows by dragging border"),
            ("cursor.zoom_factor", "Zoom Factor", "Screen zoom level (1.0 = off)"),
            ("cursor.inactive_timeout", "Cursor Timeout", "Seconds before cursor hides"),
            ("cursor.no_warps", "No Warps", "Disable cursor warping"),
        ]
        for key, label, desc in keys:
            if key not in self.schema:
                continue
            row = self._make_row(key, label, desc)
            if row:
                self.add_row(row)

    def _make_row(self, key, label, desc):
        s = self.schema[key]
        current = self.settings.get(key, s.get("default", 0))
        typ = s.get("type", "string")
        row = Adw.ActionRow(title=label, subtitle=desc)

        if typ in ("int",):
            adj = Gtk.Adjustment(value=int(current) if isinstance(current, (int, float)) else 0, lower=s.get("min", 0), upper=s.get("max", 100), step_increment=1)
            spin = Gtk.SpinButton(adjustment=adj)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, int(w.get_value())))
            row.add_suffix(spin)
        elif typ in ("float",):
            adj = Gtk.Adjustment(value=float(current) if isinstance(current, (int, float)) else 0.5, lower=0.0, upper=1.0, step_increment=0.01)
            spin = Gtk.SpinButton(adjustment=adj, digits=2)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, float(w.get_value())))
            row.add_suffix(spin)
        elif typ in ("bool",):
            switch = Gtk.Switch(active=bool(current))
            switch.connect("state-set", lambda w, s, k=key: self.track_change(k, s))
            switch.set_valign(Gtk.Align.CENTER)
            row.add_suffix(switch)
        elif typ in ("string",):
            entry = Gtk.Entry(text=str(current), hexpand=True)
            entry.connect("changed", lambda w, k=key: self.track_change(k, w.get_text()))
            row.add_suffix(entry)
        else:
            return None
        return row


class AppearancePage(SettingsPage):
    def __init__(self, settings: dict, schema: dict):
        super().__init__()
        self.settings = settings
        self.schema = schema
        self._build()

    def _build(self):
        keys = [
            ("decoration.rounding", "Corner Rounding", "Window corner radius"),
            ("decoration.active_opacity", "Active Opacity", "Opacity of focused windows"),
            ("decoration.inactive_opacity", "Inactive Opacity", "Opacity of unfocused windows"),
            ("decoration.fullscreen_opacity", "Fullscreen Opacity", "Opacity of fullscreen windows"),
            ("decoration.shadow.enabled", "Shadows", "Enable drop shadows"),
            ("decoration.shadow.range", "Shadow Range", "Shadow spread distance"),
            ("decoration.shadow.render_power", "Shadow Render Power", "Shadow quality"),
            ("decoration.blur.enabled", "Blur", "Enable background blur"),
            ("decoration.blur.size", "Blur Size", "Blur strength"),
            ("decoration.blur.passes", "Blur Passes", "Number of blur passes (0=off)"),
            ("decoration.dim_inactive", "Dim Inactive", "Dim unfocused windows"),
            ("decoration.dim_strength", "Dim Strength", "How much to dim"),
        ]
        for key, label, desc in keys:
            if key not in self.schema:
                continue
            row = self._make_row(key, label, desc)
            if row:
                self.add_row(row)

    def _make_row(self, key, label, desc):
        s = self.schema[key]
        current = self.settings.get(key, s.get("default", 0))
        typ = s.get("type", "string")
        row = Adw.ActionRow(title=label, subtitle=desc)

        if typ == "int":
            adj = Gtk.Adjustment(value=int(current) if isinstance(current, (int, float)) else 0, lower=s.get("min", 0), upper=s.get("max", 100), step_increment=1)
            spin = Gtk.SpinButton(adjustment=adj)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, int(w.get_value())))
            row.add_suffix(spin)
        elif typ == "float":
            adj = Gtk.Adjustment(value=float(current) if isinstance(current, (int, float)) else 1.0, lower=0.0, upper=1.0, step_increment=0.01)
            spin = Gtk.SpinButton(adjustment=adj, digits=2)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, float(w.get_value())))
            row.add_suffix(spin)
        elif typ == "bool":
            switch = Gtk.Switch(active=bool(current))
            switch.connect("state-set", lambda w, s, k=key: self.track_change(k, s))
            switch.set_valign(Gtk.Align.CENTER)
            row.add_suffix(switch)
        else:
            return None
        return row


class MonitorsPage(SettingsPage):
    def __init__(self, monitors: list[dict]):
        super().__init__()
        self.monitors = monitors
        self._build()

    def _build(self):
        for m in self.monitors:
            label = f"{m.get('output', 'unknown')} — {m.get('mode', 'auto')}"
            row = Adw.ActionRow(title=label, subtitle=f"Scale: {m.get('scale', 1)} | Pos: {m.get('position', '0x0')}")
            self.add_row(row)


class InputPage(SettingsPage):
    def __init__(self, settings: dict, schema: dict):
        super().__init__()
        self.settings = settings
        self.schema = schema
        self._build()

    def _build(self):
        keys = [
            ("input.kb_layout", "Keyboard Layout", "e.g. us, hu, de"),
            ("input.kb_variant", "Keyboard Variant", "e.g. qwerty, nodeadkeys"),
            ("input.kb_options", "Keyboard Options", "e.g. grp:alt_shift_toggle"),
            ("input.natural_scroll", "Natural Scroll", "Reverse scroll direction"),
            ("input.follow_mouse", "Follow Mouse", "Mouse focus behavior (0-3)"),
            ("input.repeat_rate", "Repeat Rate", "Key repeat rate (chars/sec)"),
            ("input.repeat_delay", "Repeat Delay", "Delay before repeat starts (ms)"),
            ("input.accel_profile", "Accel Profile", "Mouse acceleration profile"),
            ("input.sensitivity", "Sensitivity", "Mouse sensitivity (-1 to 1)"),
            ("input.scroll_factor", "Scroll Factor", "Scroll speed multiplier"),
            ("input.touchpad.natural_scroll", "Touchpad Natural Scroll", ""),
            ("input.touchpad.tap_to_click", "Tap to Click", ""),
            ("input.touchpad.disable_while_typing", "Disable While Typing", ""),
            ("input.touchpad.middle_button_emulation", "Middle Click Emulation", ""),
            ("input.touchpad.clickfinger_behavior", "Clickfinger Behavior", ""),
        ]
        for key, label, desc in keys:
            if key not in self.schema:
                continue
            row = self._make_row(key, label, desc)
            if row:
                self.add_row(row)

    def _make_row(self, key, label, desc):
        s = self.schema[key]
        current = self.settings.get(key, s.get("default", ""))
        typ = s.get("type", "string")
        row = Adw.ActionRow(title=label, subtitle=desc)

        if typ == "bool":
            switch = Gtk.Switch(active=bool(current))
            switch.connect("state-set", lambda w, s, k=key: self.track_change(k, s))
            switch.set_valign(Gtk.Align.CENTER)
            row.add_suffix(switch)
        elif typ in ("int",):
            adj = Gtk.Adjustment(value=int(current) if isinstance(current, (int, float)) else 0, lower=s.get("min", 0), upper=s.get("max", 100), step_increment=1)
            spin = Gtk.SpinButton(adjustment=adj)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, int(w.get_value())))
            row.add_suffix(spin)
        elif typ == "float":
            adj = Gtk.Adjustment(value=float(current) if isinstance(current, (int, float)) else 0.0, lower=-1.0, upper=1.0, step_increment=0.01)
            spin = Gtk.SpinButton(adjustment=adj, digits=2)
            spin.connect("value-changed", lambda w, k=key: self.track_change(k, float(w.get_value())))
            row.add_suffix(spin)
        elif typ == "string":
            entry = Gtk.Entry(text=str(current), hexpand=True)
            entry.connect("changed", lambda w, k=key: self.track_change(k, w.get_text()))
            row.add_suffix(entry)
        else:
            return None
        return row


class KeybindsPage(SettingsPage):
    def __init__(self, binds: list[dict]):
        super().__init__()
        self.add_row(Adw.ActionRow(title=f"{len(binds)} keybinds loaded", subtitle="Full keybind editor coming soon"))


class RulesPage(SettingsPage):
    def __init__(self, window_rules: list[dict], layer_rules: list[dict]):
        super().__init__()
        self.add_row(Adw.ActionRow(title=f"{len(window_rules)} window rules, {len(layer_rules)} layer rules", subtitle="Full rules editor coming soon"))


class AutostartPage(SettingsPage):
    def __init__(self, autostarts: list[str]):
        super().__init__()
        for cmd in autostarts:
            self.add_row(Adw.ActionRow(title=cmd))


class EnvironmentPage(SettingsPage):
    def __init__(self, env: dict):
        super().__init__()
        for k, v in env.items():
            self.add_row(Adw.ActionRow(title=k, subtitle=v))


class HyprSettingsApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id="com.hypr.settings", flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        config = read_all_configs()
        schema = load_schema()

        sidebar_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.pages = []

        def make_page(label, icon, page):
            self.pages.append(page)
            return (label, icon, page)

        page_defs = [
            make_page("General", "preferences-system-symbolic", GeneralPage(config["settings"], schema)),
            make_page("Appearance", "preferences-desktop-theme-symbolic", AppearancePage(config["settings"], schema)),
            make_page("Monitors", "video-display-symbolic", MonitorsPage(config["monitors"])),
            make_page("Input", "input-keyboard-symbolic", InputPage(config["settings"], schema)),
            make_page("Keybinds", "input-keyboard-symbolic", KeybindsPage(config["binds"])),
            make_page("Rules", "preferences-system-windows-symbolic", RulesPage(config["window_rules"], config["layer_rules"])),
            make_page("Autostart", "system-run-symbolic", AutostartPage(config["autostarts"])),
            make_page("Environment", "preferences-system-symbolic", EnvironmentPage(config["env"])),
        ]

        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.page_map = {}

        for i, (label, icon_name, page) in enumerate(page_defs):
            row = Adw.ActionRow(title=label)
            row.add_prefix(Gtk.Image(icon_name=icon_name, pixel_size=20))
            sidebar_list.append(row)

            nav_page = Adw.NavigationPage(title=label)
            nav_page.set_child(page)
            self.content_stack.add_child(nav_page)
            self.page_map[row] = nav_page

            if i == 0:
                self.content_stack.set_visible_child(nav_page)

        sidebar_list.connect("row-selected", self.on_sidebar_select)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_child(sidebar_list)
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        sidebar_nav = Adw.NavigationPage(title="Settings")
        sidebar_nav.set_child(sidebar_scroll)

        content_nav = Adw.NavigationPage(title="")
        content_nav.set_child(self.content_stack)

        self.nav_split = Adw.NavigationSplitView()
        self.nav_split.set_hexpand(True)
        self.nav_split.set_vexpand(True)
        self.nav_split.props.sidebar = sidebar_nav
        self.nav_split.props.content = content_nav

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_save)

        header = Adw.HeaderBar()
        header.pack_end(save_btn)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self.nav_split)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(toolbar)

        self.window = Adw.Window(
            application=app,
            title="HyprSettings",
            default_width=900,
            default_height=650,
        )
        self.window.set_content(self.toast_overlay)
        self.window.present()

    def on_sidebar_select(self, box, row):
        if row and row in self.page_map:
            self.content_stack.set_visible_child(self.page_map[row])

    def on_save(self, _btn):
        create_backup()
        config = read_all_configs()
        merged = dict(config["settings"])
        for page in self.pages:
            merged.update(page.changes)
        written = write_settings(merged)
        self.toast_overlay.add_toast(Adw.Toast.new(f"Saved {len(merged)} settings"))
