from typing import List
import csv
from pathlib import Path


def generate_csv_report(
    data: List[List[str]],
    save_path: str | Path,
    table_headers: List[str]
) -> None:
    save_path = Path(save_path)
    with open(save_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(
            f,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL
        )
        writer.writerow(table_headers)
        writer.writerows(data)
