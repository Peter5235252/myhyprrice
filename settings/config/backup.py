import shutil, time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "hypr"
BACKUP_DIR = CONFIG_DIR / "settings" / "backups"
SOURCE_FILES = ["state.lua", "visuals.lua", "keybinds.lua", "rules.lua", "autostart.lua", "custom.lua", "hyprpaper.conf"]

def create() -> str:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / ts
    dest.mkdir()
    for fname in SOURCE_FILES:
        src = CONFIG_DIR / fname
        if src.exists():
            shutil.copy2(src, dest / fname)
    return ts

def list_backups() -> list[dict]:
    if not BACKUP_DIR.exists():
        return []
    backups = []
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
        if d.is_dir():
            files = [f.name for f in d.iterdir() if f.is_file()]
            backups.append({"id": d.name, "files": files})
    return backups

def restore(backup_id: str) -> list[str]:
    src = BACKUP_DIR / backup_id
    if not src.exists():
        return []
    restored = []
    for fname in SOURCE_FILES:
        f = src / fname
        if f.exists():
            shutil.copy2(f, CONFIG_DIR / fname)
            restored.append(fname)
    return restored

def delete(backup_id: str) -> bool:
    src = BACKUP_DIR / backup_id
    if not src.exists():
        return False
    shutil.rmtree(src)
    return True
