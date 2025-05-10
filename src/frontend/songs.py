from tkinter import ttk

from .table.card import CardManager
from .table.table import DataTable, TablePanel, TableBuffer
from ..enums import IDENT



class Table(ttk.Frame):
    """
    TODO: Тут времменно написал, чтобы можно было собрать, в точке сбоки,
     пока не ясно как сделать
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_layout()

        self.table_panel = TablePanel(parent=self, ident=IDENT.SONG_TABLE)
        self.data_table = DataTable(
            parent=self,
            ident=IDENT.SONG_TABLE,
            headers=[],
            data=[],
            stretchable_column_indices=[1, 2, 4, 5, 6]
        )
        self.buffer = TableBuffer(ident=IDENT.SONG_TABLE)

        # Этот здесь временно
        self.card_manager = CardManager(parent)

    def _setup_layout(self):
        """Настраивает `grid` для размещения элементов."""
        self.grid_columnconfigure(0, weight=1)  # колонка с таблицей
        self.grid_rowconfigure(0, weight=0)     # панель управления
        self.grid_rowconfigure(1, weight=1)     # таблица
