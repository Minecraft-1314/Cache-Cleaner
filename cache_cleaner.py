"""Launch Cache Cleaner from the package modules."""

import sys

from PyQt6.QtWidgets import QApplication, QStyleFactory

from cache_cleaner import APP_NAME, APP_ORG, MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow()
    window.raise_()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
