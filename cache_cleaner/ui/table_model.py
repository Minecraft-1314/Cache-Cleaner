"""Table model and sort/filter proxy for cache scan results."""

from PyQt6.QtCore import (
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
)

from ..core.filesystem import format_size
from ..core.i18n import I18n


class CacheTableModel(QAbstractTableModel):
    HEADER_KEYS = ("path", "size", "modified", "status", "select")
    STATUS_PENDING = "pending"
    STATUS_FAILED = "clean_failed"

    def __init__(self, lang="en", parent=None):
        super().__init__(parent)
        self._lang = lang
        self._rows = []
        self._path_rows = {}
        self._selected_paths = set()
        self._selectable = True

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADER_KEYS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        path, size, mtime_text, status_key = self._rows[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return path
            if column == 1:
                return format_size(size)
            if column == 2:
                return mtime_text
            if column == 3:
                return I18n.get_text(status_key, self._lang)
        if role == Qt.ItemDataRole.ToolTipRole and column == 0:
            return path
        if role == Qt.ItemDataRole.UserRole:
            if column == 0:
                return path.lower()
            if column == 1:
                return size
            if column == 2:
                return mtime_text
        if role == Qt.ItemDataRole.CheckStateRole and column == 4:
            return (
                Qt.CheckState.Checked
                if path in self._selected_paths
                else Qt.CheckState.Unchecked
            )
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self.HEADER_KEYS)
        ):
            return I18n.get_text(self.HEADER_KEYS[section], self._lang)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled
        if index.column() == 4:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if (
            not index.isValid()
            or index.column() != 4
            or role != Qt.ItemDataRole.CheckStateRole
            or not self._selectable
        ):
            return False
        if isinstance(value, int):
            state = Qt.CheckState(value)
        else:
            state = value
        path = self._rows[index.row()][0]
        if state == Qt.CheckState.Checked:
            self._selected_paths.add(path)
        else:
            self._selected_paths.discard(path)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        return True

    def add_item(self, path, size, mtime_text):
        if path in self._path_rows:
            return False
        row = len(self._rows)
        self.beginInsertRows(QModelIndex(), row, row)
        self._rows.append((path, size, mtime_text, self.STATUS_PENDING))
        self._path_rows[path] = row
        self.endInsertRows()
        return True

    def update_status(self, path, status_key):
        row = self._path_rows.get(path)
        if row is None:
            return
        current = self._rows[row]
        if current[3] == status_key:
            return
        self._rows[row] = (current[0], current[1], current[2], status_key)
        index = self.index(row, 3)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def remove_paths(self, paths):
        paths = set(paths)
        if not paths:
            return False
        rows = sorted(
            (row for row, (path, _, _, _) in enumerate(self._rows) if path in paths),
            reverse=True,
        )
        if not rows:
            return False
        self.layoutAboutToBeChanged.emit()
        for row in rows:
            self._rows.pop(row)
        self._path_rows = {
            path: row for row, (path, _, _, _) in enumerate(self._rows)
        }
        self._selected_paths.difference_update(paths)
        self.layoutChanged.emit()
        return True

    def clear(self):
        if not self._rows and not self._selected_paths:
            return
        self.beginResetModel()
        self._rows.clear()
        self._path_rows.clear()
        self._selected_paths.clear()
        self.endResetModel()

    def all_paths(self):
        return [path for path, _, _, _ in self._rows]

    def path_at_row(self, row):
        if 0 <= row < len(self._rows):
            return self._rows[row][0]
        return ""

    def has_path(self, path):
        return path in self._path_rows

    def size_at_path(self, path):
        row = self._path_rows.get(path)
        if row is not None:
            return self._rows[row][1]
        return 0

    def set_language(self, lang):
        if lang == self._lang:
            return
        self._lang = lang
        if self._rows:
            top_left = self.index(0, 0)
            bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(
                top_left, bottom_right, [Qt.ItemDataRole.DisplayRole]
            )
        self.headerDataChanged.emit(
            Qt.Orientation.Horizontal, 0, self.columnCount() - 1
        )

    def set_selectable(self, selectable):
        if self._selectable == selectable:
            return
        self._selectable = selectable
        if self._rows:
            top_left = self.index(0, 4)
            bottom_right = self.index(self.rowCount() - 1, 4)
            self.dataChanged.emit(
                top_left, bottom_right, [Qt.ItemDataRole.CheckStateRole]
            )

    def selected_paths(self):
        return set(self._selected_paths)

    def selected_count(self):
        return len(self._selected_paths)

    def selected_size(self):
        return sum(self.size_at_path(path) for path in self._selected_paths)

    def select_all(self):
        if not self._rows:
            return
        self._selected_paths = set(self.all_paths())
        self._emit_selection_changed()

    def clear_selection(self):
        if not self._selected_paths:
            return
        self._selected_paths.clear()
        self._emit_selection_changed()

    def set_selected_paths(self, paths):
        self._selected_paths = set(paths)
        self._emit_selection_changed()

    def _emit_selection_changed(self):
        if not self._rows:
            return
        top_left = self.index(0, 4)
        bottom_right = self.index(self.rowCount() - 1, 4)
        self.dataChanged.emit(
            top_left, bottom_right, [Qt.ItemDataRole.CheckStateRole]
        )


class CacheProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path_filter = ""
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def set_path_filter(self, text):
        self._path_filter = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._path_filter:
            return True
        source = self.sourceModel()
        if source is None:
            return True
        index = source.index(source_row, 0, source_parent)
        path = index.data(Qt.ItemDataRole.DisplayRole) or ""
        return self._path_filter in path.lower()

    def lessThan(self, left, right):
        left_value = left.data(Qt.ItemDataRole.UserRole)
        right_value = right.data(Qt.ItemDataRole.UserRole)
        if left.column() == 1:
            return (left_value or 0) < (right_value or 0)
        return str(left_value or "") < str(right_value or "")
