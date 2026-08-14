"""Ponto de entrada da aplicação desktop."""

import sys

from PySide6.QtWidgets import QApplication

from app.styles import STYLESHEET
from app.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
