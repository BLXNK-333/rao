from typing import List, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BaseReport:
    year: int
    file_format: str  # "xlsx", "xls", "csv"
    save_path: str  # каталог, куда сохраняем
    data: List[List[Any]]

    def __post_init__(self):
        # Автоматическая генерация полного пути
        filename = self.generate_filename()
        self.save_path = str(Path(self.save_path) / filename)

    def generate_filename(self) -> str:
        raise NotImplementedError("Subclasses must implement generate_filename()")


class MonthReport(BaseReport):
    month: int

    def __init__(
            self,
            month: int,
            year: int,
            file_format: str,
            save_path: str,
            data: List[List[Any]]
    ):
        self.month = month
        super().__init__(year=year, file_format=file_format, save_path=save_path, data=data)

    def generate_filename(self) -> str:
        month_names = [
            "январь", "февраль", "март", "апрель", "май", "июнь",
            "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
        ]
        name = month_names[self.month - 1]
        return f"РАО (ВОИС) {name} {self.year} г.{self.file_format}"


class QuarterReport(BaseReport):
    quarter: int

    def __init__(
            self,
            quarter: int,
            year: int,
            file_format: str,
            save_path: str,
            data: List[List[Any]]
    ):
        self.quarter = quarter
        super().__init__(year=year, file_format=file_format, save_path=save_path, data=data)

    def generate_filename(self) -> str:
        return f"РАО {self.quarter}-й квартал {self.year} г.{self.file_format}"
