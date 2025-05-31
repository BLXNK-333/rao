#!/usr/bin/env python3
"""
Импортирует все строки из q.txt в таблицу `report`.
Связь с таблицей `songs` (поле `song_id`) временно отключена.
Перед импортом таблица `report` очищается.
"""

import csv
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import delete
from datetime import datetime, time, date

from src.backend.db.base import Engine, SessionFactory
from src.backend.db.models import Report


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_time_hms_or_ms(s: str) -> time:
    try:
        return datetime.strptime(s, "%H:%M:%S").time()
    except ValueError:
        return datetime.strptime(f"00:{s}", "%H:%M:%S").time()


def row_to_report(row: list[str]) -> Report:
    (
        date_,
        time_,
        artist,
        title,
        play_duration,
        total_duration,
        composer,
        lyricist,
        program_name,
        play_count,
        genre,
        label,
    ) = (c.strip() or None for c in row)

    return Report(
        date=parse_date(date_),
        time=parse_time_hms_or_ms(time_),
        artist=artist,
        title=title,
        play_duration=parse_time_hms_or_ms(play_duration) if play_duration else None,
        total_duration=parse_time_hms_or_ms(total_duration) if total_duration else None,
        composer=composer,
        lyricist=lyricist,
        program_name=program_name,
        play_count=int(play_count) if play_count else 1,
        genre=genre,
        label=label,
        song_id=None,
    )


def load_reports(csv_path: Path) -> None:
    with SessionFactory() as session:  # type: Session
        # Очистка таблицы report
        session.execute(delete(Report))

        with csv_path.open(encoding="utf-8") as fh:
            reader = csv.reader(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                report = row_to_report(row)
                session.add(report)

        session.commit()


def main() -> None:
    try:
        csv_path = Path(sys.argv[1])
    except IndexError:
        csv_path = Path("/home/blxnk/Documents/work/RAO_examles/csv_wip/q.txt")

    if not csv_path.exists():
        sys.exit(f"Файл {csv_path} не найден.")

    load_reports(csv_path)
    print("Загрузка завершена: таблица `report` очищена и заполнена.")


if __name__ == "__main__":
    main()
