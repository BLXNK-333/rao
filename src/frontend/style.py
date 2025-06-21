from ttkthemes import ThemedStyle

TEXT_STYLES = {
    "wrap": "word",
    "font": ("Helvetica", 11),
    "bg": "#ffffff",
    "fg": "#0a0a0a",
    "insertontime": 500,
    "insertofftime": 500,
    "insertbackground": "#444444",  # Цвет курсора
    "selectbackground": "#a3d1e5",  # Синий фон выделения
    "selectforeground": "#333444",  # Белый текст при выделении
    "relief": "flat",
    "bd": 1
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

    def configure_card_styles(self):
        """Настраивает стили для Card"""
        # Метки (Label)
        self.configure("Custom.TLabel",
                       font=("Helvetica", 10, "bold"),
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

        self.configure("TabHover.TFrame", background="#d0d0d0")  # цвет при hover
        self.configure("TabHover.TLabel", background="#d0d0d0", foreground="#444444",
                       font=("Segoe UI", 12))

        # Настройка активной вкладки
        self.configure("ActiveTab.TFrame",
                       background="#e5e5e5")  # светлый серый фон для активной вкладки
        self.configure("ActiveTab.TLabel", background="#e5e5e5", foreground="black",
                       font=("Segoe UI", 12))

    def configure_term_panel_style(self):
        """Настраивает стили для панели терминала"""
        self.configure("TermPanel.TFrame", background="#dbdbdb")
        self.configure("TermPanel.TLabel", background="#dbdbdb", foreground="black",
                       font=("Arial", 10))

    def configure_tooltip_style(self):
        """Настраивает стили подсказок заголовков таблицы."""
        self.configure(
            "CustomTooltip.TLabel",
            background="#ededed",
            foreground="#333333",
            font=("Segoe UI", 9),
            padding=(8, 4),
            relief="flat",
            borderwidth=1
        )
