import sys
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow


def main():
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)
    app.setApplicationName("Telegram Cloner GUI")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
