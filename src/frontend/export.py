from tkinter import ttk


class Export(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text="Export frame", font=("Arial", 16))
        label.pack(pady=20)