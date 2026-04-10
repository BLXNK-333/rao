from ttkthemes import ThemedStyle

# Стили для текстовых полей карточки
TEXT_STYLES = {
    "wrap": "word",
    "font": ("Helvetica", 11),
    "bg": "#ffffff",
    "fg": "#0a0a0a",
    "insertontime": 500,
    "insertofftime": 500,
    "insertbackground": "#444444",  # Цвет курсора
    "selectbackground": "#abd3e5",  # Синий фон выделения
    "selectforeground": "#333333",  # Белый текст при выделении
    "relief": "flat",
    "bd": 1
}

CONTEXT_MENU_STYLES = {
    "font": ("Helvetica", 12),
    "bg": "#4e5660",
    "fg": "#f6f6f6",
    "activebackground": "#509fcf",
    "activeforeground": "#f6f6f6",
    "relief": "flat",
    "activeborderwidth": 0,
    "disabledforeground": "#777777"
}

class UIStyles(ThemedStyle):
    def __init__(self, root):
        super().__init__(root)
        self.set_theme("breeze")
        self.configure_table_styles()
        self.configure_card_styles()
        self.configure_menu_style()
        self.configure_term_panel_style()
        self.configure_tooltip_style()
        self.configure_tentry_style()

    def configure_tentry_style(self):
        # Настраиваем виджет Entry
        self.configure('TEntry',
                        foreground=TEXT_STYLES["fg"],
                        fieldbackground=TEXT_STYLES["bg"],
                        borderwidth=TEXT_STYLES["bd"],
                        relief=TEXT_STYLES["relief"])

        # Настраиваем поведение выделения по состоянию focus и !focus
        self.map("TEntry",
                  selectbackground=[
                      ("focus", TEXT_STYLES["selectbackground"]),
                      ("!focus", "#d3d3d3")  # светло-серый цвет для неактивного выделения
                  ],
                  selectforeground=[
                      ("focus", TEXT_STYLES["selectforeground"]),
                      ("!focus", "#444444")
                      # более темный серый для текста при неактивном выделении
                  ]
                  )

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

        # Цвет выделения
        self.map("Treeview",
                  background=[("selected", "#54a7d9")],
                  foreground=[("selected", "#ffffff")])

    def configure_card_styles(self):
        """Настраивает стили для Card"""
        # Метки (Label)
        self.configure("Custom.TLabel",
                       font=("Helvetica", 10, "bold"),
                       padding=(5, 2))

    def configure_menu_style(self):
        """Настраивает стиль для верхней панели и вкладок"""

        # 🔷 Верхняя тёмная панель (заголовок)
        self.configure("MenuBar.TFrame", background="#3a3f44")
        self.configure("Toggler.TLabel", background="#3a3f44", foreground="#f6f6f6")

        # 🔷 Панель кнопок (Toolbar)
        self.configure("Toolbar.TFrame", background="#3a3f44")
        self.configure("Toolbar.TLabel", background="#3a3f44", foreground="#f6f6f6")

        # ⚪ Неактивные вкладки
        self.configure("Tab.TFrame", background="#3a3f44")
        self.configure("Tab.TLabel", background="#3a3f44", foreground="#f6f6f6")

        # 🔘 Hover по вкладке
        self.configure("TabHover.TFrame", background="#4a525a")
        self.configure("TabHover.TLabel", background="#4a525a", foreground="#f6f6f6")

        # 🔹 Активная вкладка
        self.configure("ActiveTab.TFrame", background="#4f9fcf")
        self.configure("ActiveTab.TLabel", background="#4f9fcf", foreground="#f6f6f6",
                       font=("Segoe UI", 12))

    def configure_term_panel_style(self):
        """Настраивает стили для панели терминала"""
        self.configure("TermPanel.TFrame", background="#44494f")
        self.configure("TermPanel.TLabel", background="#44494f", foreground="#fdfdfd",
                       font=("Arial", 10))

    def configure_tooltip_style(self):
        """Настраивает стили подсказок заголовков таблицы."""
        self.configure(
            "CustomTooltip.TLabel",
            background="#495056",  # тёмный фон
            foreground="#fdfdfd",  # светлый текст
            font=("Segoe UI", 10),  # современный UI-шрифт
            padding=(10, 6),
            relief="flat"
        )
