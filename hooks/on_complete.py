"""
on_complete.py — Pipeline tamamlanınca çalışır.
Terminal özeti, JSON log kaydı, opsiyonel bildirim.
"""

import json
from pathlib import Path
from datetime import datetime

from loguru import logger

BASE_DIR = Path(__file__).parent.parent
HISTORY_FILE = BASE_DIR / "output" / "logs" / "history.json"


def notify(session_id: str, drive_result: dict, script: dict = None):
    """Pipeline tamamlanınca özet yaz ve log'a kaydet."""

    entry = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "title": script.get("title", "?") if script else "?",
        "duration": script.get("total_duration", 0) if script else 0,
        "drive_file_id": drive_result.get("file_id"),
        "drive_link": drive_result.get("web_link"),
        "drive_name": drive_result.get("name"),
    }

    _append_to_history(entry)

    print("\n" + "=" * 50)
    print(f"VIDEO TAMAMLANDI: {entry['title']}")
    print(f"  Session    : {session_id}")
    print(f"  Süre       : {entry['duration']:.1f}sn")
    print(f"  Drive link : {entry['drive_link']}")
    print(f"  Zaman      : {entry['timestamp']}")
    print("=" * 50 + "\n")

    logger.success(f"Pipeline tamamlandı: {session_id} → {entry['drive_link']}")
    return entry


def _append_to_history(entry: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(entry)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Test
    notify(
        session_id="test_20260417",
        drive_result={"file_id": "abc123", "web_link": "https://drive.google.com/file/d/abc123", "name": "test.mp4"},
        script={"title": "Test Konusu", "total_duration": 42.5},
    )
