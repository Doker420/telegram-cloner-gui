from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from src.ui.themes import apply_theme
from src.config import load_settings, load_accounts
from src.core.accounts import AccountManager
from src.core.cloner import ClonerEngine
from src.workers import AsyncWorker
from src.ui.accounts_page import AccountsPage
from src.ui.chats_page import ChatsPage
from src.ui.clone_page import ClonePage
from src.ui.settings_page import SettingsPage
from src.ui.about_page import AboutPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Cloner GUI")
        self.resize(1100, 700)
        self.settings = load_settings()
        self.accounts_mgr = AccountManager()
        self.worker = AsyncWorker()
        self.worker.start()
        self.engine = ClonerEngine(
            api_id=self.settings.get("api_id", ""),
            api_hash=self.settings.get("api_hash", ""),
            sessions_dir="sessions",
            workdir=self.settings.get("workdir", "temp_downloads"),
        )
        self._build_ui()
        self._apply_theme(self.settings)
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        self.accounts_page = AccountsPage(self.engine, self.worker, self.accounts_mgr)
        self.tabs.addTab(self.accounts_page, "👥 Аккаунты")

        self.chats_page = ChatsPage(self.engine, self.worker, self.accounts_mgr)
        self.tabs.addTab(self.chats_page, "💬 Чаты")

        self.clone_page = ClonePage(self.engine, self.worker, self.accounts_mgr)
        self.tabs.addTab(self.clone_page, "🚀 Клонирование")

        self.settings_page = SettingsPage()
        self.tabs.addTab(self.settings_page, "⚙️ Настройки")

        self.about_page = AboutPage()
        self.tabs.addTab(self.about_page, "ℹ️ О программе")

    def _connect_signals(self):
        self.accounts_page.accountsChanged.connect(self._on_accounts_changed)
        self.accounts_page.statusChanged.connect(self.chats_page.refresh_accounts)
        self.accounts_page.statusChanged.connect(self.clone_page.refresh_accounts)
        self.chats_page.selectionChanged.connect(self._on_selection_changed)
        self.settings_page.settingsChanged.connect(self._on_settings_changed)
        self.worker.signals.finished.connect(self._on_worker_finished)
        self.worker.signals.error.connect(self._on_worker_error)
        self.worker.signals.event.connect(self._on_worker_event)
        QTimer.singleShot(0, self._on_accounts_changed)

    def _on_accounts_changed(self):
        accounts = self.accounts_mgr.all()
        self.chats_page.refresh_accounts(accounts)
        self.clone_page.refresh_accounts(accounts)

    def _on_selection_changed(self):
        sel = self.chats_page.get_selection()
        self.clone_page.set_selection(sel)

    def _on_settings_changed(self, data):
        self.settings = data
        self._apply_theme(self.settings)
        # Update engine
        self.engine.api_id = data.get("api_id", "")
        self.engine.api_hash = data.get("api_hash", "")
        # Update settings page fields in clone page etc if needed

    def _apply_theme(self, settings):
        from PyQt6.QtWidgets import QApplication
        theme = settings.get("theme", "dark")
        accent = settings.get("accent_color", "")
        bg = settings.get("bg_color", "")
        text = settings.get("text_color", "")
        font_size = settings.get("font_size", 13)
        apply_theme(
            QApplication.instance(),
            theme,
            accent_color=accent or None,
            bg_color=bg or None,
            text_color=text or None,
            font_size=font_size,
        )

    def _on_worker_finished(self, token, result):
        # Dispatch to pages based on token
        if token.startswith("auth_send_") or token.startswith("auth_signin_") or token.startswith("auth_pwd_"):
            self.accounts_page._on_finished(token, result)
        elif token.startswith("connect_") or token.startswith("close_"):
            self.accounts_page._on_finished(token, result)
        elif token.startswith("dialogs_"):
            self.chats_page._on_finished(token, result)
        elif token.startswith("clone_"):
            self.clone_page._on_finished(token, result)

    def _on_worker_error(self, token, error):
        if token.startswith("auth_") or token.startswith("connect_") or token.startswith("close_"):
            self.accounts_page._on_error(token, error)
        elif token.startswith("dialogs_"):
            self.chats_page._on_error(token, error)
        elif token.startswith("clone_"):
            self.clone_page._on_error(token, error)

    def _on_worker_event(self, token, payload):
        if token.startswith("clone_"):
            self.clone_page._on_event(token, payload)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Выход",
            "Завершить работу и отключиться от аккаунтов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import asyncio
                loop = self.worker.loop
                if loop and loop.is_running():
                    fut = asyncio.run_coroutine_threadsafe(self.engine.close_all(), loop)
                    fut.result(timeout=5)
            except Exception:
                pass
            self.worker.stop()
            event.accept()
        else:
            event.ignore()
