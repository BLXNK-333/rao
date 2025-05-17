from tkinter import ttk

from .table.card import CardManager
from .table.table import DataTable, TablePanel, TableBuffer
from ..enums import GROUP



class Table(ttk.Frame):
    """
    TODO: Тут времменно написал, чтобы можно было собрать, в точке сбоки,
     пока не ясно как сделать
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_layout()

        self.table_panel = TablePanel(parent=self, group=GROUP.SONG_TABLE)
        self.data_table = DataTable(parent=self, group=GROUP.SONG_TABLE)
        self.buffer = TableBuffer(group=GROUP.SONG_TABLE)

        # Этот здесь временно
        self.card_manager = CardManager(parent)

    def _setup_layout(self):
        """Настраивает `grid` для размещения элементов."""
        self.grid_columnconfigure(0, weight=1)  # колонка с таблицей
        self.grid_rowconfigure(0, weight=0)     # панель управления
        self.grid_rowconfigure(1, weight=1)     # таблица
