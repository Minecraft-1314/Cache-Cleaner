"""Launch Cache Cleaner from the package modules."""

from PyQt6.QtWidgets import QApplication, QStyleFactory

from cache_cleaner import MainWindow


def main():
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow()
    app.exec()


if __name__ == "__main__":
    main()
