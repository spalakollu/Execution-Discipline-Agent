import json
from pathlib import Path

DEFAULT_STATE = {
    "history": []
}

def load_memory(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return DEFAULT_STATE.copy()
    return json.loads(p.read_text())

def save_memory(path: str, state: dict):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))
