#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.app import HyprSettingsApp

app = HyprSettingsApp()
app.run(sys.argv)
