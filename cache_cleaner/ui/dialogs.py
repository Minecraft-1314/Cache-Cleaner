"""Small dialogs used by the main window."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QVBoxLayout
)

from ..core.config import IGNORE_DIALOG_MIN_WIDTH
from ..core.i18n import I18n


class ExcludeRulesDialog(QDialog):
    def __init__(self, parent, patterns, lang):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle(I18n.get_text("exclude_rules", self.lang))
        self.setMinimumWidth(IGNORE_DIALOG_MIN_WIDTH)
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.addItems(patterns)
        layout.addWidget(self.list_widget)
        self.hint_label = QLabel()
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label)
        self._refresh_hint()

        input_layout = QHBoxLayout()
        self.rule_input = QLineEdit()
        self.rule_input.setPlaceholderText(I18n.get_text("rule_placeholder", self.lang))
        add_btn = QPushButton(I18n.get_text("add_rule", self.lang))
        add_btn.clicked.connect(self.add_rule)
        input_layout.addWidget(self.rule_input, 1)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        remove_btn = QPushButton(I18n.get_text("remove_rule", self.lang))
        remove_btn.clicked.connect(self.remove_rule)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def add_rule(self):
        text = self.rule_input.text().strip()
        if text and not self.list_widget.findItems(text, Qt.MatchFlag.MatchExactly):
            self.list_widget.addItem(text)
            self.rule_input.clear()
        self._refresh_hint()

    def remove_rule(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self._refresh_hint()

    def _refresh_hint(self):
        is_empty = self.list_widget.count() == 0
        self.hint_label.setVisible(is_empty)
        if is_empty:
            self.hint_label.setText(I18n.get_text("no_rules", self.lang))

    def get_patterns(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
