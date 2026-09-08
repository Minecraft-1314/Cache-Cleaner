"""Dark and light application themes."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

try:
    import darkdetect
    _DARKDETECT_AVAILABLE = True
except ImportError:
    _DARKDETECT_AVAILABLE = False


DARK_QSS = """
QWidget { background-color: #121212; color: #e0e0e0; }
QPushButton { background-color: #2c2c2c; border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; }
QPushButton:hover { background-color: #3c3c3c; }
QPushButton:pressed { background-color: #505050; }
QPushButton:disabled { color: #707070; }
QProgressBar { border: none; border-radius: 6px; background-color: #2c2c2c; text-align: center; height: 10px; }
QProgressBar::chunk { background-color: #00bcd4; border-radius: 6px; }
QLineEdit, QPlainTextEdit, QTableView, QComboBox { background-color: #1e1e1e; border: 1px solid #3c3c3c; border-radius: 6px; padding: 4px; color: #e0e0e0; }
QLineEdit:focus, QComboBox:focus { border-color: #00bcd4; }
QHeaderView::section { background-color: #2c2c2c; padding: 4px; border: none; }
QTableView { gridline-color: #3c3c3c; }
QTableView::item { padding: 4px; }
QComboBox::drop-down { border: none; }
QStatusBar { background-color: #121212; color: #e0e0e0; }
QCheckBox { color: #e0e0e0; }
QCheckBox::indicator { width: 18px; height: 18px; }
QListWidget { background-color: #1e1e1e; color: #e0e0e0; }
"""

LIGHT_QSS = """
QWidget { background-color: #f5f5f5; color: #202020; }
QPushButton { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 8px; padding: 8px 16px; font-size: 13px; }
QPushButton:hover { background-color: #e0e0e0; }
QPushButton:pressed { background-color: #cccccc; }
QPushButton:disabled { color: #909090; }
QProgressBar { border: 1px solid #d0d0d0; border-radius: 6px; background-color: #ffffff; text-align: center; height: 10px; }
QProgressBar::chunk { background-color: #0088cc; border-radius: 6px; }
QLineEdit, QPlainTextEdit, QTableView, QComboBox { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 6px; padding: 4px; color: #202020; }
QLineEdit:focus, QComboBox:focus { border-color: #0088cc; }
QHeaderView::section { background-color: #f0f0f0; padding: 4px; border: none; }
QTableView { gridline-color: #d0d0d0; }
QTableView::item { padding: 4px; }
QComboBox::drop-down { border: none; }
QStatusBar { background-color: #f5f5f5; color: #202020; }
QCheckBox { color: #202020; }
QCheckBox::indicator { width: 18px; height: 18px; }
QListWidget { background-color: #ffffff; color: #202020; }
"""


def system_is_dark():
    return _DARKDETECT_AVAILABLE and darkdetect.isDark()


def apply_theme(window, dark):
    app = QApplication.instance()
    if dark:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(18, 18, 18))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 200, 200))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(palette)
        window.setStyleSheet(DARK_QSS)
        window.title_label.setStyleSheet(
            "color: #00e5ff; border-bottom: 2px solid #00e5ff; padding-bottom: 4px;"
        )
        window.subtitle_label.setStyleSheet("color: #aaaaaa;")
    else:
        app.setPalette(QApplication.style().standardPalette())
        window.setStyleSheet(LIGHT_QSS)
        window.title_label.setStyleSheet(
            "color: #0055aa; border-bottom: 2px solid #0055aa; padding-bottom: 4px;"
        )
        window.subtitle_label.setStyleSheet("color: #666666;")
