"""Tiny JSON file store for board events."""

import json
import uuid
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "events.json"


def load_events() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_events(events: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")


def add_event(event: dict) -> dict:
    events = load_events()
    event = {**event, "id": event.get("id") or f"evt_{uuid.uuid4().hex[:6]}"}
    event.setdefault("is_sample", False)
    events.insert(0, event)
    save_events(events)
    return event


def get_event(event_id: str) -> dict | None:
    return next((e for e in load_events() if e.get("id") == event_id), None)
