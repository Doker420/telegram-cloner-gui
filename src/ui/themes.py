from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


THEMES = {
    "dark": {
        "name": "Тёмная",
        "window": "#181a20",
        "base": "#22252b",
        "alternate": "#262932",
        "text": "#e6e6f0",
        "disabled_text": "#7a7f8a",
        "highlight": "#7c4dff",
        "highlighted_text": "#ffffff",
        "border": "#2e323a",
        "button": "#2a2d35",
        "button_text": "#e6e6f0",
        "link": "#80cbc4",
    },
    "light": {
        "name": "Светлая",
        "window": "#f5f5f7",
        "base": "#ffffff",
        "alternate": "#f0f0f3",
        "text": "#1c1c1e",
        "disabled_text": "#8e8e93",
        "highlight": "#7c4dff",
        "highlighted_text": "#ffffff",
        "border": "#d1d1d6",
        "button": "#ffffff",
        "button_text": "#1c1c1e",
        "link": "#0066cc",
    },
}


def apply_theme(app, theme_name, accent_color=None, bg_color=None, text_color=None, font_size=13):
    if theme_name == "custom":
        t = {
            "window": bg_color or "#181a20",
            "base": bg_color or "#181a20",
            "alternate": bg_color or "#181a20",
            "text": text_color or "#e6e6f0",
            "disabled_text": "#7a7f8a",
            "highlight": accent_color or "#7c4dff",
            "highlighted_text": "#ffffff",
            "border": "#2e323a",
            "button": bg_color or "#181a20",
            "button_text": text_color or "#e6e6f0",
            "link": "#80cbc4",
        }
    else:
        t = dict(THEMES.get(theme_name, THEMES["dark"]))
        if accent_color:
            t["highlight"] = accent_color

    stylesheet = f"""
    QWidget {{
        background-color: {t['window']};
        color: {t['text']};
        font-size: {font_size}pt;
        font-family: Segoe UI, Roboto, Arial;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {t['base']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 4px 8px;
        selection-background-color: {t['highlight']};
        selection-color: {t['highlighted_text']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['base']};
        color: {t['text']};
        selection-background-color: {t['highlight']};
        selection-color: {t['highlighted_text']};
        border: 1px solid {t['border']};
    }}
    QPushButton {{
        background-color: {t['button']};
        color: {t['button_text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t['highlight']};
        color: {t['highlighted_text']};
        border-color: {t['highlight']};
    }}
    QPushButton:pressed {{
        background-color: {t['highlight']};
        color: {t['highlighted_text']};
    }}
    QPushButton:disabled {{
        background-color: {t['alternate']};
        color: {t['disabled_text']};
        border-color: {t['border']};
    }}
    QTabWidget::pane {{
        border: 1px solid {t['border']};
        background: {t['base']};
        border-radius: 6px;
    }}
    QTabBar::tab {{
        background: {t['button']};
        color: {t['text']};
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background: {t['highlight']};
        color: {t['highlighted_text']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {t['alternate']};
    }}
    QGroupBox {{
        border: 1px solid {t['border']};
        border-radius: 8px;
        margin-top: 12px;
        font-weight: 600;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 6px;
        color: {t['highlight']};
    }}
    QProgressBar {{
        background-color: {t['base']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        text-align: center;
        color: {t['text']};
    }}
    QProgressBar::chunk {{
        background-color: {t['highlight']};
        border-radius: 6px;
    }}
    QTableWidget, QListWidget, QTreeWidget {{
        background-color: {t['base']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        selection-background-color: {t['highlight']};
        selection-color: {t['highlighted_text']};
        outline: none;
    }}
    QHeaderView::section {{
        background-color: {t['button']};
        color: {t['text']};
        padding: 4px;
        border: 1px solid {t['border']};
        font-weight: 600;
    }}
    QScrollBar:vertical {{
        background: {t['base']};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 5px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {t['base']};
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['border']};
        border-radius: 5px;
        min-width: 20px;
    }}
    QCheckBox, QRadioButton {{
        spacing: 6px;
        color: {t['text']};
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {t['border']};
        border-radius: 4px;
        background: {t['base']};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {t['highlight']};
        border-color: {t['highlight']};
    }}
    QToolTip {{
        background-color: {t['button']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 4px;
        padding: 4px;
    }}
    """
    app.setStyleSheet(stylesheet)

    # Accent palette for standard widgets
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(t["base"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t["alternate"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["button"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(t["button"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t["button_text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
    palette.setColor(QPalette.ColorRole.Link, QColor(t["link"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t["highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t["highlighted_text"]))
    app.setPalette(palette)
