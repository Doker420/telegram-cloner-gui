from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, Qt


class AuthDialog(QDialog):
    sendCodeRequested = pyqtSignal(str)
    signInRequested = pyqtSignal(str, str, str)
    passwordRequested = pyqtSignal(str)

    def __init__(self, parent=None, session_name="", phone=""):
        super().__init__(parent)
        self.session_name = session_name
        self.phone = phone
        self.phone_code_hash = None
        self.user = None
        self.setWindowTitle("Авторизация")
        self.setModal(True)
        self.setMinimumWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.phone_edit = QLineEdit(self.phone)
        self.phone_edit.setPlaceholderText("+79991234567")
        form.addRow("Телефон:", self.phone_edit)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("12345")
        self.code_edit.setEnabled(False)
        form.addRow("Код:", self.code_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль 2FA (если есть)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setEnabled(False)
        form.addRow("Пароль:", self.password_edit)

        layout.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        btns = QHBoxLayout()
        self.send_btn = QPushButton("Отправить код")
        self.send_btn.clicked.connect(self._on_send_code)
        btns.addWidget(self.send_btn)

        self.signin_btn = QPushButton("Войти")
        self.signin_btn.clicked.connect(self._on_sign_in)
        self.signin_btn.setEnabled(False)
        btns.addWidget(self.signin_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)

    def _on_send_code(self):
        phone = self.phone_edit.text().strip()
        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите номер телефона")
            return
        self.send_btn.setEnabled(False)
        self.signin_btn.setEnabled(False)
        self.status_label.setText("Отправка кода...")
        self.sendCodeRequested.emit(phone)

    def _on_sign_in(self):
        code = self.code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "Ошибка", "Введите код")
            return
        if self.password_edit.isEnabled():
            pwd = self.password_edit.text().strip()
            if not pwd:
                QMessageBox.warning(self, "Ошибка", "Введите пароль 2FA")
                return
            self.passwordRequested.emit(pwd)
        else:
            self.signin_btn.setEnabled(False)
            self.status_label.setText("Вход...")
            self.signInRequested.emit(self.phone_edit.text().strip(), code, self.phone_code_hash or "")

    def on_code_sent(self, phone_code_hash):
        self.phone_code_hash = phone_code_hash
        self.code_edit.setEnabled(True)
        self.signin_btn.setEnabled(True)
        self.status_label.setText("Код отправлен. Введите код из Telegram.")
        self.code_edit.setFocus()

    def on_code_error(self, error):
        self.send_btn.setEnabled(True)
        self.signin_btn.setEnabled(False)
        self.status_label.setText(f"Ошибка: {error}")

    def on_need_password(self):
        self.password_edit.setEnabled(True)
        self.signin_btn.setEnabled(True)
        self.status_label.setText("Введите пароль 2FA")
        self.password_edit.setFocus()

    def on_sign_in_success(self, user):
        self.user = user
        self.accept()

    def on_sign_in_error(self, error):
        self.signin_btn.setEnabled(True)
        self.status_label.setText(f"Ошибка: {error}")

    def get_user(self):
        return self.user
