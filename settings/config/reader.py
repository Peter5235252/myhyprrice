import re, json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "hypr"

class LuaTableParser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def skip_whitespace(self):
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c in " \t\r\n,":
                self.pos += 1
            elif c == "-" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "-":
                self.pos += 2
                if self.pos < len(self.text) and self.text[self.pos] == "[":
                    self.pos += 1
                    while self.pos < len(self.text) and self.text[self.pos] != "]":
                        self.pos += 1
                    if self.pos < len(self.text):
                        self.pos += 1
                else:
                    while self.pos < len(self.text) and self.text[self.pos] != "\n":
                        self.pos += 1
            else:
                break

    def parse_string(self):
        if self.text[self.pos] == '"':
            self.pos += 1
            s = ""
            while self.pos < len(self.text) and self.text[self.pos] != '"':
                if self.text[self.pos] == "\\":
                    self.pos += 1
                    if self.pos < len(self.text):
                        s += self.text[self.pos]
                        self.pos += 1
                else:
                    s += self.text[self.pos]
                    self.pos += 1
            self.pos += 1
            return s
        elif self.text[self.pos] == "'":
            self.pos += 1
            s = ""
            while self.pos < len(self.text) and self.text[self.pos] != "'":
                if self.text[self.pos] == "\\":
                    self.pos += 1
                    if self.pos < len(self.text):
                        s += self.text[self.pos]
                        self.pos += 1
                else:
                    s += self.text[self.pos]
                    self.pos += 1
            self.pos += 1
            return s
        return None

    def parse_value(self):
        self.skip_whitespace()
        if self.pos >= len(self.text):
            return None

        c = self.text[self.pos]
        if c in "\"'":
            return self.parse_string()
        elif c == "{":
            return self.parse_table()
        elif c.isdigit() or c == "-":
            start = self.pos
            if self.text[self.pos] == "-":
                self.pos += 1
            while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == "."):
                self.pos += 1
            s = self.text[start:self.pos]
            return float(s) if "." in s else int(s)
        elif c == "t":
            if self.text[self.pos:self.pos+4] == "true":
                self.pos += 4
                return True
        elif c == "f":
            if self.text[self.pos:self.pos+5] == "false":
                self.pos += 5
                return False
        elif c == "n":
            if self.text[self.pos:self.pos+4] == "nil":
                self.pos += 4
                return None
        else:
            m = re.match(r'[a-zA-Z_][\w.]*(?:\([^)]*\))?', self.text[self.pos:])
            if m:
                ident = m.group()
                if ident.startswith("rgba(") or ident.startswith("rgb("):
                    self.pos += len(ident)
                    return ident
                if "(" in ident:
                    self.pos += len(ident)
                    return ident
                self.pos += len(ident)
                return ident
        return None

    def parse_table(self):
        self.pos += 1
        result = {}
        idx = 1
        while self.pos < len(self.text):
            self.skip_whitespace()
            if self.pos >= len(self.text):
                break
            if self.text[self.pos] == "}":
                self.pos += 1
                return result

            self.skip_whitespace()
            key = None
            is_array = False

            if self.text[self.pos] == "[":
                self.pos += 1
                self.skip_whitespace()
                if self.text[self.pos] in "\"'":
                    key = self.parse_string()
                else:
                    m = re.match(r'\d+', self.text[self.pos:])
                    if m:
                        key = int(m.group())
                        self.pos += len(m.group())
                    else:
                        key = None
                self.skip_whitespace()
                if self.pos < len(self.text) and self.text[self.pos] == "]":
                    self.pos += 1
                self.skip_whitespace()
                if self.pos < len(self.text) and self.text[self.pos] == "=":
                    self.pos += 1
            elif re.match(r'[a-zA-Z_]', self.text[self.pos:]):
                m = re.match(r'([a-zA-Z_]\w*)\s*=', self.text[self.pos:])
                if m:
                    key = m.group(1)
                    self.pos += m.end()
                else:
                    is_array = True
                    key = idx
                    idx += 1
            else:
                is_array = True
                key = idx
                idx += 1

            if key is not None:
                val = self.parse_value()
                if val is not None:
                    if isinstance(key, int) and is_array:
                        result[str(key)] = val
                    else:
                        result[key] = val
        return result


def extract_hl_config_blocks(text: str) -> list[dict]:
    blocks = []
    pattern = r'hl\.config\s*\(\s*(\{)'
    for m in re.finditer(pattern, text):
        start = m.start(1)
        parser = LuaTableParser(text[start:])
        try:
            table = parser.parse_table()
            if isinstance(table, dict):
                blocks.append(table)
        except Exception:
            pass
    return blocks


def flatten_table(data: dict, prefix: str = "") -> dict:
    result = {}
    for k, v in data.items():
        pk = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_table(v, pk))
        else:
            result[pk] = v
    return result


def extract_monitors(text: str) -> list[dict]:
    monitors = []
    pattern = r'hl\.monitor\s*\(\s*(\{)'
    for m in re.finditer(pattern, text):
        start = m.start(1)
        parser = LuaTableParser(text[start:])
        try:
            table = parser.parse_table()
            if isinstance(table, dict):
                monitors.append(table)
        except Exception:
            pass
    return monitors


def extract_env_vars(text: str) -> dict:
    env = {}
    pattern = r'hl\.env\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)'
    for m in re.finditer(pattern, text):
        env[m.group(1)] = m.group(2)
    pattern = r"hl\.env\s*\(\s*'([^']+)'\s*,\s*'([^']*)'\s*\)"
    for m in re.finditer(pattern, text):
        env[m.group(1)] = m.group(2)
    return env


def extract_binds(text: str) -> list[dict]:
    binds = []
    pattern = r'hl\.bind\s*\(\s*"([^"]+)"\s*,\s*([^)]+)\s*(?:,\s*(\{[^}]*\})\s*)?\)'
    for m in re.finditer(pattern, text):
        keys = m.group(1)
        dispatcher = m.group(2).strip()
        opts = m.group(3)
        binds.append({"keys": keys, "dispatcher": dispatcher, "options": opts})
    return binds


def extract_window_rules(text: str) -> list[dict]:
    rules = []
    pattern = r'hl\.window_rule\s*\(\s*(\{)'
    for m in re.finditer(pattern, text):
        start = m.start(1)
        parser = LuaTableParser(text[start:])
        try:
            table = parser.parse_table()
            if isinstance(table, dict):
                rules.append(table)
        except Exception:
            pass
    return rules


def extract_layer_rules(text: str) -> list[dict]:
    rules = []
    pattern = r'hl\.layer_rule\s*\(\s*(\{)'
    for m in re.finditer(pattern, text):
        start = m.start(1)
        parser = LuaTableParser(text[start:])
        try:
            table = parser.parse_table()
            if isinstance(table, dict):
                rules.append(table)
        except Exception:
            pass
    return rules


def extract_autostarts(text: str) -> list[str]:
    autostarts = []
    pattern = r'hl\.on\s*\(\s*"hyprland\.start"\s*,\s*function\s*\(\)\s*((?:[^{}]|\{[^{}]*\})*)\s*end\s*\)'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        body = m.group(1)
        for cmd in re.finditer(r'hl\.exec_cmd\s*\(\s*"([^"]+)"\s*\)', body):
            autostarts.append(cmd.group(1))
        for cmd in re.finditer(r"hl\.exec_cmd\s*\(\s*'([^']+)'\s*\)", body):
            autostarts.append(cmd.group(1))
    return autostarts


def read_all_configs() -> dict:
    result = {
        "settings": {},
        "monitors": [],
        "env": {},
        "binds": [],
        "window_rules": [],
        "layer_rules": [],
        "autostarts": [],
        "files": {},
    }

    files_to_read = ["state.lua", "visuals.lua", "keybinds.lua", "rules.lua", "autostart.lua", "custom.lua"]

    for fname in files_to_read:
        path = CONFIG_DIR / fname
        if not path.exists():
            continue
        text = path.read_text()
        result["files"][fname] = text

        blocks = extract_hl_config_blocks(text)
        for block in blocks:
            flat = flatten_table(block)
            result["settings"].update(flat)

        if fname in ("visuals.lua", "custom.lua"):
            result["monitors"].extend(extract_monitors(text))
            result["env"].update(extract_env_vars(text))

        if fname in ("keybinds.lua",):
            result["binds"].extend(extract_binds(text))

        if fname in ("rules.lua",):
            result["window_rules"].extend(extract_window_rules(text))
            result["layer_rules"].extend(extract_layer_rules(text))

        if fname in ("autostart.lua",):
            result["autostarts"].extend(extract_autostarts(text))

    return result


if __name__ == "__main__":
    config = read_all_configs()
    print(json.dumps(config, indent=2, default=str))
