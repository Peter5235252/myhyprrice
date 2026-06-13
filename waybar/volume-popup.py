#!/usr/bin/env python3
import sys
import os
import subprocess

# Toggle check: close existing instance if already open
current_pid = os.getpid()
try:
    pids = subprocess.check_output(["pgrep", "-f", "volume-popup.py"]).decode().strip().split()
    for pid in pids:
        if int(pid) != current_pid:
            subprocess.run(["kill", pid])
            sys.exit(0)
except Exception:
    pass

# Run natively under Wayland
os.environ["GDK_BACKEND"] = "wayland"

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# Force Wayland app_id to be "VolumePopup" for matching window rules
GLib.set_prgname("VolumePopup")

# Custom CSS styling for the Rosé Pine palette
css_provider = Gtk.CssProvider()
css_provider.load_from_data(b"""
    window {
        background-color: #1f1d2e;  /* Surface */
        border: 2px solid #c4a7e7;  /* Iris border */
        border-radius: 12px;
    }
    scale trough {
        background-color: #26233a;  /* Overlay track */
        border-radius: 6px;
        min-width: 14px;
    }
    scale highlight {
        background-color: #c4a7e7;  /* Iris fill */
        border-radius: 6px;
    }
    scale slider {
        background-color: #ebbcba;  /* Rose handle */
        border-radius: 50%;
        min-height: 18px;
        min-width: 18px;
    }
""")

class VolumePopup(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        # Setting a unique title we can match inside hyprland.lua
        self.set_title("VolumePopup")
        self.set_keep_above(True)
        self.set_decorated(False)
        self.set_default_size(60, 220)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)

        # PipeWire Volume reading
        self.current_volume = self.get_volume()

        # Vertical Slider
        self.adjustment = Gtk.Adjustment(value=self.current_volume, lower=0, upper=100, step_increment=1, page_increment=10)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=self.adjustment)
        self.scale.set_inverted(True)
        self.scale.set_draw_value(False)
        self.scale.set_margin_top(20)
        self.scale.set_margin_bottom(20)
        self.scale.set_margin_start(15)
        self.scale.set_margin_end(15)

        self.scale.connect("value-changed", self.on_volume_changed)
        self.add(self.scale)

        # Capture clicks outside the window and keyboard presses
        self.connect("button-press-event", self.on_button_press)
        self.connect("key-press-event", self.on_key_press)
        self.connect("show", self.on_show)

        # Inject Rosé Pine CSS
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.show_all()

    def get_volume(self):
        try:
            output = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]).decode("utf-8")
            vol_str = output.split()[1]
            return int(float(vol_str) * 100)
        except Exception:
            return 50

    def on_volume_changed(self, scale):
        val = int(scale.get_value())
        subprocess.run(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{val}%"])
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])

    def on_show(self, widget):
        # Corrected widget-level grab methods
        self.grab_add()

    def on_button_press(self, widget, event):
        # Check if the click coordinates fall outside our window allocation bounds
        allocation = self.get_allocation()
        if (event.x < 0 or event.y < 0 or 
            event.x > allocation.width or event.y > allocation.height):
            self.grab_remove()
            Gtk.main_quit()
            return True
        return False

    def on_key_press(self, widget, event):
        # Allow dismissing with Escape key
        if event.keyval == Gdk.KEY_Escape:
            self.grab_remove()
            Gtk.main_quit()
            return True
        return False

if __name__ == "__main__":
    app = VolumePopup()
    Gtk.main()
