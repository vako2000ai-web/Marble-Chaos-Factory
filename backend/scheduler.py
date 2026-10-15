"""SQLite media catalog and deterministic, repeat-aware playlist scheduler.

No external dependencies. Run: python -m backend.scheduler --demo
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS media_assets (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 path TEXT NOT NULL UNIQUE,
 category TEXT NOT NULL,
 duration REAL NOT NULL CHECK(duration > 0),
 approved INTEGER NOT NULL DEFAULT 0 CHECK(approved IN (0,1))
);
CREATE TABLE IF NOT EXISTS playback_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 media_id INTEGER NOT NULL REFERENCES media_assets(id),
 played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

@dataclass(frozen=True)
class Media:
    id: int
    path: str
    category: str
    duration: float

def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db

def add_media(db: sqlite3.Connection, path: str, category: str, duration: float, approved: bool = True) -> None:
    if duration <= 0:
        raise ValueError("duration must be positive")
    db.execute(
        """INSERT INTO media_assets(path, category, duration, approved) VALUES(?,?,?,?)
        ON CONFLICT(path) DO UPDATE SET category=excluded.category,
        duration=excluded.duration, approved=excluded.approved""",
        (path, category, duration, int(approved)),
    )
    db.commit()

def choose_next(db: sqlite3.Connection, rng: random.Random | None = None, cooldown: int = 20) -> Media | None:
    """Choose an approved file; prefer assets not in recent history and vary category.

    Falls back to the oldest-shown asset when the catalog is smaller than cooldown.
    Caller must record play *only after playback begins*.
    """
    rng = rng or random.Random()
    rows = db.execute(
        "SELECT id,path,category,duration FROM media_assets WHERE approved=1 ORDER BY id"
    ).fetchall()
    if not rows:
        return None
    recent = [r[0] for r in db.execute(
        "SELECT media_id FROM playback_history ORDER BY id DESC LIMIT ?", (max(cooldown, 0),)
    )]
    eligible = [r for r in rows if r[0] not in recent]
    if not eligible:
        # If all videos are in cooldown, choose the least recently used.
        eligible = sorted(rows, key=lambda r: recent.index(r[0]) if r[0] in recent else 10**9, reverse=True)
        eligible = eligible[:1]
    last = db.execute(
        "SELECT m.category FROM playback_history p JOIN media_assets m ON m.id=p.media_id ORDER BY p.id DESC LIMIT 1"
    ).fetchone()
    if last:
        alternate = [r for r in eligible if r[2] != last[0]]
        if alternate:
            eligible = alternate
    row = rng.choice(eligible)
    return Media(*row)

def record_playback(db: sqlite3.Connection, media_id: int) -> None:
    db.execute("INSERT INTO playback_history(media_id) VALUES(?)", (media_id,))
    db.commit()

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/database/media.sqlite")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    with connect(args.db) as db:
        if args.demo:
            for n, category in enumerate(["spiral", "funnel", "race", "avalanche"]):
                add_media(db, f"DEMO_ONLY_{n}.mp4", category, 30)
            for _ in range(8):
                media = choose_next(db)
                if media:
                    print(f"Next: {media.path} [{media.category}]")
                    record_playback(db, media.id)
        else:
            print("Media catalog initialized:", args.db)

if __name__ == "__main__":
    main()
