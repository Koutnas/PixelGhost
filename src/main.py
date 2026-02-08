from Stegui import MainUI
from PyQt6.QtWidgets import QApplication
import sys


def main():
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()