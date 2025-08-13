import json
from pathlib import Path
from config import FESTIVOS_JSON

def load_festivos():
    p = Path(FESTIVOS_JSON)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("festivos", [])

def save_festivos(festivos):
    p = Path(FESTIVOS_JSON)
    with p.open("w", encoding="utf-8") as f:
        json.dump({"festivos": festivos}, f, indent=2, ensure_ascii=False)
