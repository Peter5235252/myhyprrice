import subprocess, json, re
from pathlib import Path

HYPRCTL = "hyprctl"

def get(key: str) -> dict | None:
    hyprctl_key = key.replace(".", ":")
    try:
        r = subprocess.run(
            [HYPRCTL, "getoption", hyprctl_key],
            capture_output=True, text=True, timeout=2
        )
        if r.returncode != 0:
            return None
        return _parse_getoption(r.stdout.strip())
    except Exception:
        return None

def _parse_getoption(output: str) -> dict:
    result = {"raw": output}
    first = output.split("\n")[0].strip()

    if first.startswith("int: "):
        result["type"] = "int"
        result["value"] = int(first.split(": ", 1)[1])
    elif first.startswith("float: "):
        result["type"] = "float"
        result["value"] = float(first.split(": ", 1)[1])
    elif first.startswith("string: "):
        result["type"] = "string"
        result["value"] = first.split(": ", 1)[1]
    elif first == "bool: true":
        result["type"] = "bool"
        result["value"] = True
    elif first == "bool: false":
        result["type"] = "bool"
        result["value"] = False
    elif first.startswith("css gap data:"):
        result["type"] = "css_gaps"
        result["value"] = first.split(": ", 1)[1].strip()
    else:
        result["type"] = "unknown"
        result["value"] = output

    result["set"] = "set: true" in output or "set: false" in output
    return result

def set_value(key: str, value) -> bool:
    hyprctl_key = key.replace(".", ":")
    try:
        r = subprocess.run(
            [HYPRCTL, "keyword", hyprctl_key, str(value)],
            capture_output=True, text=True, timeout=2
        )
        return r.returncode == 0
    except Exception:
        return False

def reload() -> bool:
    try:
        r = subprocess.run(
            [HYPRCTL, "reload"],
            capture_output=True, text=True, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False

def get_monitors() -> list[dict]:
    try:
        r = subprocess.run(
            [HYPRCTL, "monitors", "-j"],
            capture_output=True, text=True, timeout=2
        )
        return json.loads(r.stdout)
    except Exception:
        return []

def get_binds() -> list[dict]:
    try:
        r = subprocess.run(
            [HYPRCTL, "binds", "-j"],
            capture_output=True, text=True, timeout=2
        )
        return json.loads(r.stdout)
    except Exception:
        return []

def get_clients() -> list[dict]:
    try:
        r = subprocess.run(
            [HYPRCTL, "clients", "-j"],
            capture_output=True, text=True, timeout=2
        )
        return json.loads(r.stdout)
    except Exception:
        return []

def get_devices() -> dict:
    try:
        r = subprocess.run(
            [HYPRCTL, "devices", "-j"],
            capture_output=True, text=True, timeout=2
        )
        return json.loads(r.stdout)
    except Exception:
        return {}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "get"
    if cmd == "get" and len(sys.argv) > 2:
        print(json.dumps(get(sys.argv[2]), indent=2))
    elif cmd == "set" and len(sys.argv) > 3:
        val = sys.argv[3]
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
        print(set_value(sys.argv[2], val))
    elif cmd == "reload":
        print(reload())
    elif cmd == "monitors":
        print(json.dumps(get_monitors(), indent=2))
    elif cmd == "binds":
        print(json.dumps(get_binds(), indent=2))
    elif cmd == "clients":
        print(json.dumps(get_clients(), indent=2))
    elif cmd == "devices":
        print(json.dumps(get_devices(), indent=2))
