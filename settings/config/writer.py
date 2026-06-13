import json, re
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "hypr"
OVERRIDES_PATH = CONFIG_DIR / "settings" / "overrides.lua"


def write_overrides(settings: dict) -> None:
    lines = ["-- HyprSettings overrides — auto-generated, do not edit manually", ""]

    schema_path = Path(__file__).parent.parent / "schema.json"
    schema = json.loads(schema_path.read_text()) if schema_path.exists() else {}

    complex_cats = {"gradient", "vec2", "css_gaps"}
    skip_prefixes = set()
    for k, info in schema.items():
        if info.get("type", "") in complex_cats:
            skip_prefixes.add(k + ".")

    simple_keys = {}
    for key, val in settings.items():
        if _is_corrupted(key):
            continue
        if any(key.startswith(p) for p in skip_prefixes):
            continue
        info = schema.get(key, {})
        if info.get("type", "") in complex_cats:
            continue
        simple_keys[key] = val

    def _val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(v)
        if isinstance(v, str):
            if v.startswith("rgba(") or v.startswith("rgb("):
                return v
            return json.dumps(v)
        return str(v)

    sections = {}
    for key, val in simple_keys.items():
        parts = key.split(".")
        sec = parts[0]
        if sec not in sections:
            sections[sec] = {}
        node = sections[sec]
        for p in parts[1:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = val

    def _render(d, indent=1):
        pad = "    " * (indent + 1)
        close = "    " * indent
        items = []
        for k, v in d.items():
            if isinstance(v, dict):
                items.append(f"{pad}{k} = {_render(v, indent + 1)},")
            else:
                items.append(f"{pad}{k} = {_val(v)},")
        return "{\n" + "\n".join(items) + "\n" + close + "}"

    config_parts = []
    for sec, tree in sorted(sections.items()):
        if tree:
            config_parts.append(f"    {sec} = {_render(tree)},")

    if config_parts:
        lines.append("hl.config({")
        lines.extend(config_parts)
        lines.append("})")
        lines.append("")

    OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_PATH.write_text("\n".join(lines) + "\n")


def ensure_require_in_entrypoint() -> bool:
    ep = CONFIG_DIR / "hyprland.lua"
    if not ep.exists():
        return False
    text = ep.read_text()
    marker = 'pcall(require, "settings.overrides")'
    if marker in text:
        return False
    text = text.rstrip() + f"\n\n{marker}\n"
    ep.write_text(text)
    return True


def write_settings(settings: dict) -> list[str]:
    write_overrides(settings)
    ensure_require_in_entrypoint()
    return ["overrides.lua"]


RESPONSE_FIELDS = {"raw", "type", "value", "set"}


def _is_corrupted(key: str) -> bool:
    parts = key.split(".")
    return any(p in RESPONSE_FIELDS for p in parts)


def read_overrides() -> dict:
    if not OVERRIDES_PATH.exists():
        return {}
    text = OVERRIDES_PATH.read_text()
    from config.reader import extract_hl_config_blocks, flatten_table
    blocks = extract_hl_config_blocks(text)
    if not blocks:
        return {}
    raw = flatten_table(blocks[0])
    return {k: v for k, v in raw.items() if not _is_corrupted(k)}


def write_changes(changes: dict) -> None:
    existing = read_overrides()
    existing.update(changes)
    _write_nested(existing)


def remove_overrides(keys: list[str]) -> None:
    existing = read_overrides()
    for key in keys:
        existing.pop(key, None)
    _write_nested(existing)


def _write_nested(data: dict) -> None:
    lines = ["-- HyprSettings overrides — auto-generated, do not edit manually", ""]
    if not data:
        OVERRIDES_PATH.write_text("\n".join(lines) + "\n")
        return

    sections = {}
    for key, val in data.items():
        parts = key.split(".")
        sec = parts[0]
        if sec not in sections:
            sections[sec] = {}
        node = sections[sec]
        for p in parts[1:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        if isinstance(val, (bool, int, float, str)):
            node[parts[-1]] = val
        else:
            node[parts[-1]] = str(val)

    def _val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(v)
        if isinstance(v, str):
            if v.startswith("rgba(") or v.startswith("rgb("):
                return v
            return json.dumps(v)
        return str(v)

    def _render(d, indent=1):
        pad = "    " * (indent + 1)
        close = "    " * indent
        items = []
        for k, v in d.items():
            if isinstance(v, dict):
                items.append(f"{pad}{k} = {_render(v, indent + 1)},")
            else:
                items.append(f"{pad}{k} = {_val(v)},")
        return "{\n" + "\n".join(items) + "\n" + close + "}"

    config_parts = []
    for sec, tree in sorted(sections.items()):
        if tree:
            config_parts.append(f"    {sec} = {_render(tree)},")

    if config_parts:
        lines.append("hl.config({")
        lines.extend(config_parts)
        lines.append("})")
        lines.append("")

    OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_PATH.write_text("\n".join(lines) + "\n")


def write_env(env: dict) -> list[str]:
    return []


def write_monitors(monitors: list[dict]) -> list[str]:
    return []
