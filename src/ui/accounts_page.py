import uuid
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from src.core.accounts import AccountManager, parse_proxy


class AccountsPage(QWidget):
    accountsChanged = pyqtSignal()
    statusChanged = pyqtSignal(str, str)

    def __init__(self, engine, worker, accounts_mgr, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.worker = worker
        self.accounts = accounts_mgr
        self._pending = {}
        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить аккаунт")
        self.remove_btn = QPushButton("🗑 Удалить")
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.remove_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Имя", "Сессия", "Прокси", "Статус", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._add_account)
        self.remove_btn.clicked.connect(self._remove_account)
        self.worker.signals.finished.connect(self._on_finished)
        self.worker.signals.error.connect(self._on_error)

    def refresh(self):
        self.table.setRowCount(0)
        for acc in self.accounts.all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(acc.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, acc["id"])
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(acc.get("session", "")))
            self.table.setItem(row, 2, QTableWidgetItem(acc.get("proxy", "")))
            status_item = QTableWidgetItem("Не подключен")
            status_item.setForeground(QColor("#7a7f8a"))
            self.table.setItem(row, 3, status_item)

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)

            connect_btn = QPushButton("Подключить")
            connect_btn.clicked.connect(lambda _, s=acc["id"]: self._connect_account(s))
            al.addWidget(connect_btn)

            proxy_btn = QPushButton("Прокси")
            proxy_btn.clicked.connect(lambda _, s=acc["id"]: self._edit_proxy(s))
            al.addWidget(proxy_btn)

            self.table.setCellWidget(row, 4, actions)

    def _current_account_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_account(self):
        temp_session = f"temp_{uuid.uuid4().hex[:8]}"
        from src.ui.auth_dialog import AuthDialog
        dialog = AuthDialog(self, session_name=temp_session)
        dialog.sendCodeRequested.connect(lambda phone: self._on_send_code(dialog, temp_session, phone))
        dialog.signInRequested.connect(lambda phone, code, hash: self._on_sign_in(dialog, temp_session, phone, code, hash))
        dialog.passwordRequested.connect(lambda pwd: self._on_check_password(dialog, temp_session, pwd))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user = dialog.get_user()
            if user:
                name = user.get("first_name", "") or temp_session
                if user.get("username"):
                    name = f"{name} (@{user['username']})"
                session_name = f"acc_{user['id']}"
                old_path = Path("sessions") / f"{temp_session}.session"
                new_path = Path("sessions") / f"{session_name}.session"
                if old_path.exists():
                    if new_path.exists():
                        new_path.unlink()
                    old_path.rename(new_path)
                if temp_session in self.engine._clients:
                    client = self.engine._clients.pop(temp_session)
                    self.engine._clients[session_name] = client
                self.accounts.add(name, session_name, "")
                self.refresh()
                self.accountsChanged.emit()

    def _on_send_code(self, dialog, session_name, phone):
        token = f"auth_send_{session_name}"
        self._pending[token] = ("dialog", dialog)
        self.worker.submit(token, self.engine.send_code(session_name, phone))

    def _on_sign_in(self, dialog, session_name, phone, code, phone_code_hash):
        token = f"auth_signin_{session_name}"
        self._pending[token] = ("dialog", dialog)
        self.worker.submit(token, self.engine.sign_in(session_name, phone, code, phone_code_hash))

    def _on_check_password(self, dialog, session_name, password):
        token = f"auth_pwd_{session_name}"
        self._pending[token] = ("dialog", dialog)
        self.worker.submit(token, self.engine.check_password(session_name, password))

    def _connect_account(self, acc_id):
        acc = self.accounts.get(acc_id)
        if not acc:
            return
        proxy = acc.get("proxy", "")
        token = f"connect_{acc_id}"
        self._pending[token] = ("connect", acc_id)
        self.worker.submit(token, self.engine.ensure_connected(acc["session"], proxy))

    def _edit_proxy(self, acc_id):
        acc = self.accounts.get(acc_id)
        if not acc:
            return
        proxy_str, ok = QInputDialog.getText(self, "Прокси", "Введите прокси (scheme://[user:pass@]host:port):", text=acc.get("proxy", ""))
        if not ok:
            return
        try:
            parse_proxy(proxy_str)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return
        self.accounts.update_proxy(acc_id, proxy_str)
        self.refresh()
        self.accountsChanged.emit()

    def _remove_account(self):
        acc_id = self._current_account_id()
        if not acc_id:
            QMessageBox.warning(self, "Ошибка", "Выберите аккаунт")
            return
        acc = self.accounts.get(acc_id)
        if not acc:
            return
        confirm = QMessageBox.question(self, "Удаление", f"Удалить аккаунт {acc.get('name', '')}?")
        if confirm == QMessageBox.StandardButton.Yes:
            session = acc.get("session")
            if session and session in self.engine._clients:
                self.worker.submit(f"close_{acc_id}", self.engine.close(session))
            self.accounts.remove(acc_id)
            self.refresh()
            self.accountsChanged.emit()

    def _on_finished(self, token, result):
        ctx = self._pending.pop(token, None)
        if not ctx:
            return
        ctx_type, data = ctx

        if token.startswith("auth_send_"):
            if isinstance(result, dict) and "phone_code_hash" in result:
                data.on_code_sent(result["phone_code_hash"])
            else:
                data.on_code_error(result.get("error", str(result)) if isinstance(result, dict) else str(result))
        elif token.startswith("auth_signin_"):
            if isinstance(result, dict) and result.get("ok"):
                data.on_sign_in_success(result.get("user", {}))
            elif isinstance(result, dict) and result.get("need_password"):
                data.on_need_password()
            else:
                data.on_sign_in_error(result.get("error", str(result)) if isinstance(result, dict) else str(result))
        elif token.startswith("auth_pwd_"):
            if isinstance(result, dict) and result.get("ok"):
                data.on_sign_in_success(result.get("user", {}))
            else:
                data.on_sign_in_error(result.get("error", str(result)) if isinstance(result, dict) else str(result))
        elif token.startswith("connect_"):
            acc_id = token[len("connect_"):]
            status = "Подключен" if isinstance(result, dict) and result.get("ok") else f"Ошибка: {result.get('error', result) if isinstance(result, dict) else result}"
            self._set_status(acc_id, status)
            self.statusChanged.emit(acc_id, status)

    def _on_error(self, token, error):
        ctx = self._pending.pop(token, None)
        if not ctx:
            return
        ctx_type, data = ctx
        if ctx_type == "dialog":
            if token.startswith("auth_send_"):
                data.on_code_error(error)
            elif token.startswith("auth_signin_"):
                data.on_sign_in_error(error)
            elif token.startswith("auth_pwd_"):
                data.on_sign_in_error(error)
        elif ctx_type == "connect":
            acc_id = token[len("connect_"):]
            self._set_status(acc_id, f"Ошибка: {error}")
            self.statusChanged.emit(acc_id, f"Ошибка: {error}")

    def _set_status(self, acc_id, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == acc_id:
                status_item = QTableWidgetItem(text)
                if "Подключен" in text:
                    status_item.setForeground(QColor("#4caf50"))
                else:
                    status_item.setForeground(QColor("#f44336"))
                self.table.setItem(row, 3, status_item)
                break
