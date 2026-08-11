import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QColorDialog, QComboBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from src.config import load_settings, save_settings


class SettingsPage(QWidget):
    settingsChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = load_settings()
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        appearance = QGroupBox("Оформление")
        form_a = QFormLayout(appearance)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмная", "Светлая", "Пользовательская"])
        form_a.addRow("Тема:", self.theme_combo)
        self.accent_edit = QLineEdit()
        self.accent_btn = QPushButton("...")
        self.accent_btn.setFixedWidth(30)
        self.accent_btn.clicked.connect(self._pick_color(self.accent_edit))
        accent_layout = QHBoxLayout()
        accent_layout.addWidget(self.accent_edit)
        accent_layout.addWidget(self.accent_btn)
        form_a.addRow("Акцентный цвет:", accent_layout)
        self.bg_edit = QLineEdit()
        self.bg_btn = QPushButton("...")
        self.bg_btn.setFixedWidth(30)
        self.bg_btn.clicked.connect(self._pick_color(self.bg_edit))
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(self.bg_edit)
        bg_layout.addWidget(self.bg_btn)
        form_a.addRow("Фон:", bg_layout)
        self.text_edit = QLineEdit()
        self.text_btn = QPushButton("...")
        self.text_btn.setFixedWidth(30)
        self.text_btn.clicked.connect(self._pick_color(self.text_edit))
        text_layout = QHBoxLayout()
        text_layout.addWidget(self.text_edit)
        text_layout.addWidget(self.text_btn)
        form_a.addRow("Текст:", text_layout)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        form_a.addRow("Размер шрифта:", self.font_spin)
        layout.addWidget(appearance)

        default_opts = QGroupBox("Настройки по умолчанию")
        form_d = QFormLayout(default_opts)
        self.api_id_edit = QLineEdit()
        form_d.addRow("API ID:", self.api_id_edit)
        self.api_hash_edit = QLineEdit()
        form_d.addRow("API Hash:", self.api_hash_edit)
        self.bot_link_edit = QLineEdit()
        form_d.addRow("Ссылка на бота:", self.bot_link_edit)
        self.hashtags_edit = QLineEdit()
        form_d.addRow("Хэштеги:", self.hashtags_edit)
        self.delay_min = QDoubleSpinBox()
        self.delay_min.setRange(0, 60)
        form_d.addRow("Задержка мин:", self.delay_min)
        self.delay_max = QDoubleSpinBox()
        self.delay_max.setRange(0, 60)
        form_d.addRow("Задержка макс:", self.delay_max)
        self.workdir_edit = QLineEdit()
        self.workdir_btn = QPushButton("Обзор...")
        self.workdir_btn.clicked.connect(self._browse_workdir)
        wd_layout = QHBoxLayout()
        wd_layout.addWidget(self.workdir_edit)
        wd_layout.addWidget(self.workdir_btn)
        form_d.addRow("Рабочая папка:", wd_layout)
        layout.addWidget(default_opts)

        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch()

    def _pick_color(self, edit):
        def _inner():
            color = QColorDialog.getColor(QColor(edit.text()), self, "Выберите цвет")
            if color.isValid():
                edit.setText(color.name().lower())
        return _inner

    def _browse_workdir(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите рабочую папку")
        if d:
            self.workdir_edit.setText(d)

    def _load(self):
        s = self.settings
        theme = s.get("theme", "dark")
        if theme == "dark":
            self.theme_combo.setCurrentIndex(0)
        elif theme == "light":
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(2)
        self.accent_edit.setText(s.get("accent_color", ""))
        self.bg_edit.setText(s.get("bg_color", ""))
        self.text_edit.setText(s.get("text_color", ""))
        self.font_spin.setValue(s.get("font_size", 13))
        self.api_id_edit.setText(str(s.get("api_id", "")))
        self.api_hash_edit.setText(s.get("api_hash", ""))
        self.bot_link_edit.setText(s.get("bot_link", ""))
        self.hashtags_edit.setText(" ".join(s.get("hashtags", [])))
        self.delay_min.setValue(float(s.get("delay_min", 2)))
        self.delay_max.setValue(float(s.get("delay_max", 8)))
        self.workdir_edit.setText(s.get("workdir", "temp_downloads"))

    def _save(self):
        theme_idx = self.theme_combo.currentIndex()
        theme_map = {0: "dark", 1: "light", 2: "custom"}
        data = {
            "theme": theme_map.get(theme_idx, "dark"),
            "accent_color": self.accent_edit.text().strip(),
            "bg_color": self.bg_edit.text().strip(),
            "text_color": self.text_edit.text().strip(),
            "font_size": self.font_spin.value(),
            "api_id": self.api_id_edit.text().strip(),
            "api_hash": self.api_hash_edit.text().strip(),
            "bot_link": self.bot_link_edit.text().strip(),
            "hashtags": [h.strip() for h in self.hashtags_edit.text().split() if h.strip()],
            "delay_min": self.delay_min.value(),
            "delay_max": self.delay_max.value(),
            "workdir": self.workdir_edit.text().strip(),
        }
        save_settings(data)
        self.settings = data
        self.settingsChanged.emit(data)
        QMessageBox.information(self, "Сохранено", "Настройки сохранены")

    def current_settings(self):
        return self.settings
