import sys
from pathlib import Path

import tkinter as tk

from ...enums import ICON


class Icons:
    # EFF0F1 - dark fg
    # 3D3D3D - dark bg

    _file_map = {
        ICON.ADD_CARD_24: "plus-24.png",
        ICON.EDIT_CARD_24: "pencil-24.png",
        ICON.DELETE_CARD_24: "delete-24.png",
        ICON.AUTO_SIZE_ON_24: "double-arrow-on-24.png",
        ICON.AUTO_SIZE_OFF_24: "double-arrow-off-24.png",
        ICON.ERASER_24: "eraser-24.png",

        ICON.SONGS_LIST_24: "list-music-24.png",
        ICON.REPORT_LIST_24: "checklist-task-budget-24.png",
        ICON.EXPORT_24: "xls-file-24.png",
        ICON.SETTINGS_24: "settings-24.png",

        ICON.TERMINAL_LIGHT_24: "square-terminal-light-24.png",
        ICON.TERMINAL_DARK_24: "square-terminal-dark-24.png",
        ICON.TERMINAL_LIGHT_DOT_24: "square-terminal-light-dot-24.png",
        ICON.TERMINAL_DARK_DOT_24: "square-terminal-dark-dot-24.png",

        ICON.STOP_RED_16: "round-16.png",
        ICON.STOP_GRAY_16: "circle-16.png",
        ICON.CLEAR_16: "c-16.png",
        ICON.TERM_SMALL_LIGHT_16: "square-s-light-16.png",
        ICON.TERM_SMALL_DARK_16: "square-s-dark-16.png",
        ICON.TERM_MEDIUM_LIGHT_16: "square-m-light-16.png",
        ICON.TERM_MEDIUM_DARK_16: "square-m-dark-16.png",
        ICON.TERM_LARGE_LIGHT_16: "square-l-light-16.png",
        ICON.TERM_LARGE_DARK_16: "square-l-dark-16.png",
        ICON.CLOSE_16: "cross-16.png",

        ICON.FOLDER_16: "folder-open-16.png"
    }
    _instance = None
    _loaded = False

    def __new__(cls):
        """Ensure a single instance of the Icons class."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the Icons class and load the icons if not already loaded (Singleton).
        """

        if not self._loaded:
            self._icons_dir = self._get_icon_dir()
            self._map = {}
            self._load_icons()
            self._loaded = True

    def _load_icons(self):
        """Load icons from the specified directory."""
        for icon, filename in self._file_map.items():
            path = self._icons_dir / filename
            self._map[icon] = tk.PhotoImage(file=path)

    def __getitem__(self, icon: ICON) -> tk.PhotoImage:
        """Return the PhotoImage for the given icon."""
        return self._map.get(icon)

    @staticmethod
    def _get_icon_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / "src" / "frontend" / "icons"
        return Path(__file__).parent
