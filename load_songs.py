#!/usr/bin/env python3
"""
Populate the `songs` table from m.txt.

The script is idempotent: if a song with the same (artist, title) pair
already exists, it will be skipped.
"""

import csv
import sys
from datetime import time
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

# ---- project imports -------------------------------------------------------
from src.backend.db.base import Engine, SessionFactory          # noqa: E402
from src.backend.db.models import Songs                         # noqa: E402
# ----------------------------------------------------------------------------


def normalize_duration(s: str) -> time:
    minutes, seconds = map(int, s.strip().split(":"))
    return time(hour=0, minute=minutes, second=seconds)


def load_songs(csv_path: Path) -> None:
    with SessionFactory() as session:
        # Очищаем таблицу
        session.execute(delete(Songs))

        seen = set()
        with csv_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(";")
                if len(parts) != 6:
                    print(f"⚠️ Строка невалидна: {line}")
                    continue

                artist, title, duration_str, composer, lyricist, label = [
                    p.strip() or None for p in parts]
                duration = normalize_duration(duration_str)
                row_key = (artist, title, duration_str, composer, lyricist, label)

                if row_key in seen:
                    continue
                seen.add(row_key)

                song = Songs(
                    artist=artist,
                    title=title,
                    duration=duration,
                    composer=composer,
                    lyricist=lyricist,
                    label=label,
                )
                session.add(song)

        session.commit()


def main() -> None:
    try:
        csv_path = Path(sys.argv[1])
    except IndexError:
        csv_path = Path("/home/blxnk/Documents/work/RAO_examles/csv_wip/m.txt")

    if not csv_path.exists():
        sys.exit(f"Файл {csv_path} не найден.")

    load_songs(csv_path)
    print("Загрузка в таблицу `songs` завершена.")


def debug():
    csv_path = Path("/home/blxnk/Documents/work/RAO_examles/csv_wip/m.txt")
    with csv_path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue

            parts = line.split(";")

            if len(parts[2]) != 5:
                print(i, parts)


if __name__ == "__main__":
    main()
    # debug()