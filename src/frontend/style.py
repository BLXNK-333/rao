from tkinter import ttk


class UIStyles(ttk.Style):
    def __init__(self):
        super().__init__()
        self.theme_use("breeze")
        self.configure_table_styles()
        self.configure_card_styles()
        self.configure_menu_style()

    def configure_table_styles(self):
        """Настраивает стили для таблицы (Treeview)"""
        # Таблица
        self.configure("Treeview",
                       rowheight=25,
                       borderwidth=1,
                       relief="solid",
                       font=("Arial", 11))
        self.configure("Treeview.Heading",
                       font=("Arial", 10, "bold"))

    def configure_card_styles(self):
        """Настраивает стили для Card"""
        # Метки (Label)
        self.configure("Custom.TLabel",
                       font=("Arial", 10, "bold"),
                       padding=(5, 2))

    def configure_menu_style(self):
        """Настраивает стиль для верхней панели для светлой темы"""

        # Верхняя панель с белым фоном
        self.configure("MenuBar.TFrame", background="#dbdbdb")
        self.configure("Toggler.TLabel", background="#dbdbdb")

        # Настройка вкладки (неактивной)
        self.configure("Tab.TFrame", background="#c9c9c9")
        self.configure("Tab.TLabel", background="#c9c9c9", foreground="#444444",
                       font=("Segoe UI", 12))

        # Настройка активной вкладки
        self.configure("ActiveTab.TFrame",
                       background="#e5e5e5")  # светлый серый фон для активной вкладки
        self.configure("ActiveTab.TLabel", background="#e5e5e5", foreground="black",
                       font=("Segoe UI", 12))
