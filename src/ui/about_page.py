from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from src.config import DEV_NAME, DEV_TELEGRAM, DEV_GITHUB, LOGO_PATH


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(LOGO_PATH))
        if not pix.isNull():
            logo.setPixmap(
                pix.scaled(
                    160, 160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("🐙")
            logo.setStyleSheet("font-size: 72px;")
        layout.addWidget(logo)

        title = QLabel("Telegram Cloner GUI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22pt; font-weight: bold;")
        layout.addWidget(title)

        ver = QLabel("Версия 2.0.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        layout.addSpacing(16)

        dev_label = QLabel(f"Разработчик: {DEV_NAME}")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev_label)

        tg_btn = QPushButton(f"✈️ Telegram: {DEV_TELEGRAM}")
        tg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tg_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DEV_TELEGRAM))
        )
        layout.addWidget(tg_btn)

        gh_btn = QPushButton(f"🐙 GitHub: {DEV_GITHUB}")
        gh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gh_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DEV_GITHUB))
        )
        layout.addWidget(gh_btn)

        layout.addStretch()
