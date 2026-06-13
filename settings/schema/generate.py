import json, re, sys
from pathlib import Path

STUBS_PATH = Path("/usr/share/hypr/stubs/hl.meta.lua")
SCHEMA_OUT = Path(__file__).parent.parent / "schema.json"

FILE_MAP = {
    "general":     "visuals.lua",
    "decoration":  "visuals.lua",
    "cursor":      "visuals.lua",
    "animations":  "visuals.lua",
    "input":       "visuals.lua",
    "xwayland":    "visuals.lua",
    "misc":        "visuals.lua",
    "gestures":    "visuals.lua",
    "group":       "visuals.lua",
    "dwindle":     "visuals.lua",
    "master":      "visuals.lua",
    "scrolling":   "visuals.lua",
    "debug":       "visuals.lua",
    "opengl":      "visuals.lua",
    "render":      "visuals.lua",
    "quirks":      "visuals.lua",
    "ecosystem":   "visuals.lua",
    "experimental":"visuals.lua",
    "binds":       "keybinds.lua",
    "layout":      "keybinds.lua",
}

def parse_type(raw: str) -> str:
    t = raw.strip()
    if t == "boolean":
        return "bool"
    if t == "integer|boolean":
        return "int"
    if t == "number|boolean":
        return "float"
    if t == "integer|HL.CssGap":
        return "css_gaps"
    if t == "string|HL.Gradient":
        return "gradient"
    if t in ("HL.Vec2Like",):
        return "vec2"
    if "integer|string" in t:
        return "int_or_string"
    if t == "string":
        return "string"
    if "number" in t:
        return "float"
    if "integer" in t:
        return "int"
    return "string"

def guess_default(typ: str) -> object:
    return {
        "bool": False,
        "int": 0,
        "float": 0.0,
        "css_gaps": "0 0 0 0",
        "gradient": "",
        "vec2": "0x0",
        "string": "",
        "int_or_string": 0,
    }.get(typ, "")

def guess_min_max(typ: str) -> tuple:
    if typ == "int":
        return (0, 100)
    if typ == "float":
        return (0.0, 1.0)
    return (None, None)

def parse_stubs(text: str) -> dict:
    schema = {}
    in_value_types = False

    for line in text.splitlines():
        if "class HL.ConfigValueTypes" in line:
            in_value_types = True
            continue
        if in_value_types and ("local __HL_ConfigValueTypes" in line or "---@class" in line):
            break
        if not in_value_types:
            continue

        m = re.match(r'---@field\s+\[\'([\w.]+)\'\]\s+(.+)', line)
        if not m:
            m = re.match(r'---@field\s+\[\"([\w.]+)\"\]\s+(.+)', line)
        if not m:
            continue

        key = m.group(1)
        typ = parse_type(m.group(2).rstrip())

        category = key.split(".")[0]
        file = FILE_MAP.get(category, "visuals.lua")

        min_v, max_v = guess_min_max(typ)

        schema[key] = {
            "type": typ,
            "category": category,
            "file": file,
            "default": guess_default(typ),
        }
        if min_v is not None:
            schema[key]["min"] = min_v
        if max_v is not None:
            schema[key]["max"] = max_v

    return schema

def load_live_defaults(schema: dict) -> dict:
    import subprocess
    for key in schema:
        hyprctl_key = key.replace(".", ":")
        try:
            r = subprocess.run(
                ["hyprctl", "getoption", hyprctl_key],
                capture_output=True, text=True, timeout=2
            )
            if r.returncode != 0:
                continue
            val = r.stdout.split("\n")[0].strip()
            if val.startswith("int: "):
                schema[key]["default"] = int(val.split(": ", 1)[1])
            elif val.startswith("float: "):
                schema[key]["default"] = float(val.split(": ", 1)[1])
            elif val.startswith("string: "):
                schema[key]["default"] = val.split(": ", 1)[1]
            elif val.lower() == "bool: true":
                schema[key]["default"] = True
            elif val.lower() == "bool: false":
                schema[key]["default"] = False
            elif val.startswith("css gap data:"):
                parts = val.split(": ", 1)[1].strip()
                schema[key]["default"] = parts
        except Exception:
            pass
    return schema

text = STUBS_PATH.read_text()
schema = parse_stubs(text)
schema = load_live_defaults(schema)

SCHEMA_OUT.write_text(json.dumps(schema, indent=2))
print(f"Wrote {len(schema)} keys to {SCHEMA_OUT}")
