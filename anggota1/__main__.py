
import sys

from PySide6.QtWidgets import QApplication

from anggota1.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BPIC17 Process Mining")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
