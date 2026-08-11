from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class ChatsPage(QWidget):
    selectionChanged = pyqtSignal()

    def __init__(self, engine, worker, accounts_mgr, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.worker = worker
        self.accounts = accounts_mgr
        self._all_chats = {}
        self.selected_source_id = None
        self.selected_target_ids = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Доступные чаты:"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left_layout.addWidget(self.available_list)
        layout.addLayout(left_layout, 2)

        mid_layout = QVBoxLayout()
        mid_layout.addStretch()
        self.to_source_btn = QPushButton(">")
        self.to_source_btn.setFixedWidth(40)
        self.to_source_btn.clicked.connect(self._move_to_source)
        mid_layout.addWidget(self.to_source_btn)
        self.to_target_btn = QPushButton(">>")
        self.to_target_btn.setFixedWidth(40)
        self.to_target_btn.clicked.connect(self._move_to_targets)
        mid_layout.addWidget(self.to_target_btn)
        self.from_target_btn = QPushButton("<")
        self.from_target_btn.setFixedWidth(40)
        self.from_target_btn.clicked.connect(self._remove_from_targets)
        mid_layout.addWidget(self.from_target_btn)
        self.from_source_btn = QPushButton("<")
        self.from_source_btn.setFixedWidth(40)
        self.from_source_btn.clicked.connect(self._remove_from_source)
        mid_layout.addWidget(self.from_source_btn)
        mid_layout.addStretch()
        layout.addLayout(mid_layout, 0)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Источник:"))
        self.source_list = QListWidget()
        self.source_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        right_layout.addWidget(self.source_list)
        right_layout.addWidget(QLabel("Цели:"))
        self.target_list = QListWidget()
        self.target_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.target_list)
        layout.addLayout(right_layout, 2)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.save_btn = QPushButton("💾 Сохранить выбор")
        self.save_btn.clicked.connect(self._save_selection)
        bottom.addWidget(self.save_btn)
        layout.addLayout(bottom)

        top = QHBoxLayout()
        top.addWidget(QLabel("Аккаунт:"))
        self.account_combo = QComboBox()
        top.addWidget(self.account_combo, 1)
        self.refresh_chats_btn = QPushButton("🔄 Обновить")
        self.refresh_chats_btn.clicked.connect(self._load_chats)
        top.addWidget(self.refresh_chats_btn)
        layout.insertLayout(0, top)

    def _connect_signals(self):
        self.account_combo.currentIndexChanged.connect(self._load_chats)
        self.worker.signals.finished.connect(self._on_finished)
        self.worker.signals.error.connect(self._on_error)

    def refresh_accounts(self, accounts):
        self.account_combo.clear()
        for acc in accounts:
            self.account_combo.addItem(acc.get("name", acc.get("session", "")), acc.get("session", ""))
        if self.account_combo.count() > 0:
            self._load_chats()

    def _load_chats(self):
        session = self.account_combo.currentData()
        if not session:
            return
        self.available_list.clear()
        self.source_list.clear()
        self.target_list.clear()
        self._all_chats = {}
        self.selected_source_id = None
        self.selected_target_ids = []
        token = f"dialogs_{session}"
        self.worker.submit(token, self.engine.get_dialogs(session))

    def _on_finished(self, token, result):
        if token.startswith("dialogs_"):
            session = token[len("dialogs_"):]
            if session != self.account_combo.currentData():
                return
            self._all_chats = {}
            self.available_list.clear()
            if isinstance(result, list):
                for chat in result:
                    self._all_chats[chat["id"]] = chat
                    item = QListWidgetItem(f"{chat['title']} (@{chat['username']}) [{chat['members']}]")
                    item.setData(Qt.ItemDataRole.UserRole, chat["id"])
                    self.available_list.addItem(item)

    def _on_error(self, token, error):
        if token.startswith("dialogs_"):
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить чаты: {error}")

    def _move_to_source(self):
        item = self.available_list.currentItem()
        if not item:
            return
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if self.selected_source_id == chat_id:
            return
        self.selected_source_id = chat_id
        self.source_list.clear()
        title = self._all_chats.get(chat_id, {}).get("title", str(chat_id))
        src_item = QListWidgetItem(f"📌 {title}")
        src_item.setData(Qt.ItemDataRole.UserRole, chat_id)
        self.source_list.addItem(src_item)
        self.selectionChanged.emit()

    def _move_to_targets(self):
        for item in self.available_list.selectedItems():
            chat_id = item.data(Qt.ItemDataRole.UserRole)
            if chat_id not in self.selected_target_ids:
                self.selected_target_ids.append(chat_id)
                title = self._all_chats.get(chat_id, {}).get("title", str(chat_id))
                target_item = QListWidgetItem(f"🎯 {title}")
                target_item.setData(Qt.ItemDataRole.UserRole, chat_id)
                self.target_list.addItem(target_item)
        self.selectionChanged.emit()

    def _remove_from_source(self):
        self.selected_source_id = None
        self.source_list.clear()
        self.selectionChanged.emit()

    def _remove_from_targets(self):
        for item in self.target_list.selectedItems():
            chat_id = item.data(Qt.ItemDataRole.UserRole)
            if chat_id in self.selected_target_ids:
                self.selected_target_ids.remove(chat_id)
            row = self.target_list.row(item)
            if row >= 0:
                self.target_list.takeItem(row)
        self.selectionChanged.emit()

    def _save_selection(self):
        if not self.selected_source_id:
            QMessageBox.warning(self, "Ошибка", "Выберите источник")
            return
        if not self.selected_target_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну цель")
            return
        self.selectionChanged.emit()
        QMessageBox.information(self, "Сохранено", f"Источник: {self._all_chats.get(self.selected_source_id, {}).get('title', '')}\nЦелей: {len(self.selected_target_ids)}")

    def get_selection(self):
        return {
            "session": self.account_combo.currentData(),
            "source_id": self.selected_source_id,
            "target_ids": list(self.selected_target_ids),
            "source_title": self._all_chats.get(self.selected_source_id, {}).get("title", "") if self.selected_source_id else "",
            "target_titles": [self._all_chats.get(tid, {}).get("title", "") for tid in self.selected_target_ids],
        }
