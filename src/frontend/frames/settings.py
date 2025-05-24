from tkinter import ttk


class Settings(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text="Settings frame", font=("Arial", 16))
        label.pack(pady=20)