import json
from pathlib import Path


DEFAULT_SETTINGS = {
    "sound_on": True,
    "car_color": "blue",
    "difficulty": "normal",
    "last_username": "Player",
}


def _read_json(path, default_value):
    file_path = Path(path)
    if not file_path.exists():
        return default_value

    try:
        with file_path.open("r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (OSError, json.JSONDecodeError):
        return default_value


def _write_json(path, payload):
    file_path = Path(path)
    with file_path.open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)


def load_settings(base_dir):
    path = Path(base_dir) / "settings.json"
    payload = _read_json(path, {})
    settings = DEFAULT_SETTINGS.copy()

    if isinstance(payload, dict):
        settings.update(
            {
                "sound_on": bool(payload.get("sound_on", settings["sound_on"])),
                "car_color": str(payload.get("car_color", settings["car_color"])),
                "difficulty": str(payload.get("difficulty", settings["difficulty"])),
                "last_username": str(
                    payload.get("last_username", settings["last_username"])
                ),
            }
        )

    return settings


def save_settings(base_dir, settings):
    path = Path(base_dir) / "settings.json"
    payload = DEFAULT_SETTINGS.copy()
    payload.update(settings)
    _write_json(path, payload)


def load_leaderboard(base_dir):
    path = Path(base_dir) / "leaderboard.json"
    payload = _read_json(path, [])

    if not isinstance(payload, list):
        return []

    entries = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        entries.append(
            {
                "name": str(entry.get("name", "Player"))[:20],
                "score": int(entry.get("score", 0)),
                "distance": int(entry.get("distance", 0)),
                "coins": int(entry.get("coins", 0)),
                "difficulty": str(entry.get("difficulty", "normal")),
                "result": str(entry.get("result", "Crash")),
            }
        )
    return entries


def save_leaderboard(base_dir, entries):
    path = Path(base_dir) / "leaderboard.json"
    ordered = sorted(
        entries,
        key=lambda item: (item.get("score", 0), item.get("distance", 0)),
        reverse=True,
    )[:10]
    _write_json(path, ordered)


def add_leaderboard_entry(base_dir, entry):
    entries = load_leaderboard(base_dir)
    entries.append(
        {
            "name": str(entry.get("name", "Player"))[:20],
            "score": int(entry.get("score", 0)),
            "distance": int(entry.get("distance", 0)),
            "coins": int(entry.get("coins", 0)),
            "difficulty": str(entry.get("difficulty", "normal")),
            "result": str(entry.get("result", "Crash")),
        }
    )
    save_leaderboard(base_dir, entries)
    return load_leaderboard(base_dir)
