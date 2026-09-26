"""Main window controller."""

import html
import os
import time

from PyQt6.QtCore import (
    QSettings, Qt, QTimer, QUrl
)
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QStatusBar
)

from ..core.config import (
    APP_NAME, APP_ORG, MAX_CLEAN_PREVIEW,
    MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, SCAN_MODE_LOCATION, SCAN_MODE_SUFFIX,
    STATUS_UPDATE_INTERVAL, TABLE_UPDATE_BATCH, THEME_POLL_INTERVAL_MS,
    THREAD_QUIT_TIMEOUT_MS, get_system_language
)
from ..core.filesystem import format_size, trash_available
from ..core.i18n import I18n
from ..core.locations import LOCATION_GROUPS, first_available_location, get_cache_locations
from ..core.scanner import CacheScanEngine, DeleteThread, ScanThread
from ..core.suffixes import SUFFIX_GROUPS, get_default_suffix_tokens, get_suffix_rules
from ..ui.table_model import CacheTableModel
from .dialogs import ExcludeRulesDialog
from .theme import apply_theme as _apply_theme, system_is_dark
from .widgets import build_ui

class MainWindow(QMainWindow):
    @staticmethod
    def _read_str_list(settings, key):
        value = settings.value(key, [])
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, (list, tuple)):
            return [item for item in value if isinstance(item, str)]
        return []

    def __init__(self):
        super().__init__()
        self.settings = QSettings(APP_ORG, APP_NAME)
        self.lang = self.settings.value("language", get_system_language())
        self.theme_mode = self.settings.value("theme_mode", "system")
        self.theme_dark = (
            system_is_dark()
            if self.theme_mode == "system"
            else self.settings.value("dark_mode", False, bool)
        )
        self.scan_mode = self.settings.value("scan_mode", SCAN_MODE_LOCATION)
        if self.scan_mode not in (SCAN_MODE_LOCATION, SCAN_MODE_SUFFIX):
            self.scan_mode = SCAN_MODE_LOCATION
        self.use_trash = self.settings.value("use_trash", True, bool)
        if self.use_trash and not trash_available():
            self.use_trash = False

        self.cache_locations = get_cache_locations()
        self.suffix_rules = get_suffix_rules()

        self.selected_dirs = self._read_str_list(self.settings, "selected_dirs")
        if not self.settings.contains("selected_dirs"):
            default = first_available_location()
            self.selected_dirs = [default] if os.path.isdir(default) else []
        self.scan_root = self.settings.value("scan_root", "")
        if not os.path.isdir(self.scan_root):
            self.scan_root = ""

        self.selected_suffixes = self._read_str_list(
            self.settings, "selected_suffixes"
        )
        if not self.selected_suffixes:
            self.selected_suffixes = get_default_suffix_tokens()

        self.ignored_paths_raw = set(
            self._read_str_list(self.settings, "ignored_paths")
        )
        self.exclude_patterns = self._read_str_list(
            self.settings, "exclude_patterns"
        )

        self.engine = CacheScanEngine(
            scan_roots=self.selected_dirs, scan_mode=self.scan_mode, lang=self.lang
        )
        self.engine.set_selected_suffixes(self.selected_suffixes)
        self.engine.set_ignored_paths(self.ignored_paths_raw)
        self.engine.set_ignore_patterns(self.exclude_patterns)

        self.is_running = False
        self.is_scanning = False
        self.scan_thread = None
        self.clean_thread = None
        self.current_clean_paths = []
        self.sort_column = -1
        self.sort_order = Qt.SortOrder.AscendingOrder
        self.scan_start_time = 0
        self._last_status_update = 0.0
        self._updating_scope = False
        self._scope_dirty = False

        self.setWindowTitle(I18n.get_text("title", self.lang))
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.setup_ui()
        self.setup_shortcuts()
        self.apply_theme(self.theme_dark)
        self.status_bar.showMessage(I18n.get_text("ready", self.lang))
        self.restore_geometry()
        self.show()

        self.dark_timer = QTimer(self)
        self.dark_timer.timeout.connect(self.check_system_theme)
        self.sync_theme_polling()

    def sync_theme_polling(self):
        if self.theme_mode == "system":
            self.dark_timer.start(THEME_POLL_INTERVAL_MS)
        else:
            self.dark_timer.stop()

    def check_system_theme(self):
        if self.theme_mode != "system":
            return
        current = system_is_dark()
        if current != self.theme_dark:
            self.theme_dark = current
            self.apply_theme(current)

    def closeEvent(self, event):
        self.engine.stop()
        self._shutdown_thread(self.scan_thread)
        self._shutdown_thread(self.clean_thread)
        self.save_settings()
        super().closeEvent(event)

    @staticmethod
    def _shutdown_thread(thread):
        if thread is None or not thread.isRunning():
            return
        thread.quit()
        if thread.wait(THREAD_QUIT_TIMEOUT_MS):
            return
        thread.terminate()
        thread.wait()

    def save_settings(self):
        self.settings.setValue("language", self.lang)
        self.settings.setValue("theme_mode", self.theme_mode)
        self.settings.setValue("dark_mode", self.theme_dark)
        self.settings.setValue("scan_mode", self.scan_mode)
        self.settings.setValue("selected_dirs", self.selected_dirs)
        self.settings.setValue("selected_suffixes", self.selected_suffixes)
        self.settings.setValue("scan_root", self.scan_root)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        self.settings.setValue("ignored_paths", list(self.ignored_paths_raw))
        self.settings.setValue("exclude_patterns", self.exclude_patterns)
        self.settings.setValue("use_trash", self.use_trash)

    def restore_geometry(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.showMaximized()
        splitter_state = self.settings.value("splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+A"), self, self.select_all)
        QShortcut(QKeySequence("F5"), self, self.start_scan)
        QShortcut(QKeySequence("Escape"), self, self.escape_pressed)

    def escape_pressed(self):
        if self.is_scanning:
            self.stop_scan()
        elif self.is_running:
            self.stop_clean()

    def setup_ui(self):
        build_ui(self)
        self.populate_directory_list()
        self.populate_suffix_list()
        self._scope_dirty = True
        self.directory_frame.setVisible(self.scan_mode == SCAN_MODE_LOCATION)
        self.suffix_frame.setVisible(self.scan_mode == SCAN_MODE_SUFFIX)

        self.directory_list.itemChanged.connect(self.on_directory_item_changed)
        self.suffix_list.itemChanged.connect(self.on_suffix_item_changed)
        self.model.dataChanged.connect(self._on_model_data_changed)
        self.update_scope_counts()
        self.update_texts()
    def _checkable_count(self, list_widget):
        count = 0
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                count += 1
        return count

    def _checked_values(self, list_widget):
        values = []
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if (
                item.flags() & Qt.ItemFlag.ItemIsUserCheckable
                and item.checkState() == Qt.CheckState.Checked
            ):
                values.append(item.data(Qt.ItemDataRole.UserRole))
        return values

    def _normalized_path_set(self, paths):
        return {os.path.normcase(os.path.normpath(path)) for path in paths}

    def populate_directory_list(self):
        self._updating_scope = True
        try:
            self.directory_list.clear()
            selected = self._normalized_path_set(self.selected_dirs)
            for group in LOCATION_GROUPS:
                group_locations = [loc for loc in self.cache_locations if loc.group == group]
                if not group_locations:
                    continue
                self._add_group_item(
                    self.directory_list,
                    I18n.get_text("group_" + group, self.lang),
                )
                for loc in group_locations:
                    label = loc.label(self.lang)
                    if not os.path.isdir(loc.path):
                        label += "  [" + I18n.get_text("missing_location", self.lang) + "]"
                    item = QListWidgetItem(label)
                    item.setData(Qt.ItemDataRole.UserRole, loc.path)
                    item.setToolTip(loc.path)
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if os.path.normcase(os.path.normpath(loc.path)) in selected
                        else Qt.CheckState.Unchecked
                    )
                    self.directory_list.addItem(item)
        finally:
            self._updating_scope = False

    def populate_suffix_list(self):
        self._updating_scope = True
        try:
            self.suffix_list.clear()
            selected = set(self.selected_suffixes)
            for group in SUFFIX_GROUPS:
                rules = [rule for rule in self.suffix_rules if rule.group == group]
                if not rules:
                    continue
                self._add_group_item(
                    self.suffix_list,
                    I18n.get_text("group_" + group, self.lang),
                )
                for rule in rules:
                    kind_text = I18n.get_text("rule_kind_" + rule.kind, self.lang)
                    item = QListWidgetItem(f"{rule.token}  ({kind_text})")
                    item.setData(Qt.ItemDataRole.UserRole, rule.token)
                    group_text = I18n.get_text("group_" + rule.group, self.lang)
                    tooltip = f"{group_text}: {kind_text} {rule.token}"
                    if rule.risky:
                        tooltip += "  (" + I18n.get_text("rule_risky", self.lang) + ")"
                    item.setToolTip(tooltip)
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if rule.token in selected
                        else Qt.CheckState.Unchecked
                    )
                    self.suffix_list.addItem(item)
        finally:
            self._updating_scope = False

    def pick_scan_root(self):
        if self.is_scanning or self.is_running:
            return
        start_path = self.scan_root if os.path.isdir(self.scan_root) else os.path.expanduser("~")
        selected = QFileDialog.getExistingDirectory(
            self, I18n.get_text("select_dir", self.lang), start_path
        )
        if not selected:
            return
        self.scan_root = selected
        self.scan_root_path.setText(selected)
        self._mark_scope_dirty()

    def _mark_scope_dirty(self):
        self._scope_dirty = True
        self.model.clear()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_text.setText("0 / 0")
        self.space_label.setText("")
        self.sync_ui_state()
        self.status_bar.showMessage(I18n.get_text("ready", self.lang))

    @staticmethod
    def _add_group_item(list_widget, text):
        item = QListWidgetItem("  " + text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setData(Qt.ItemDataRole.UserRole, None)
        list_widget.addItem(item)

    @staticmethod
    def _set_all_checked(list_widget, checked):
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(
                    Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )

    def on_directory_item_changed(self, item):
        if self._updating_scope:
            return
        self.selected_dirs = self._checked_values(self.directory_list)
        self.update_scope_counts()
        if not self.is_scanning and not self.is_running:
            self._mark_scope_dirty()

    def on_suffix_item_changed(self, item):
        if self._updating_scope:
            return
        self.selected_suffixes = self._checked_values(self.suffix_list)
        self.update_scope_counts()
        if not self.is_scanning and not self.is_running:
            self._mark_scope_dirty()

    def select_all_directories(self):
        self._set_all_checked(self.directory_list, True)
        self.on_directory_item_changed(None)

    def clear_directories(self):
        self._set_all_checked(self.directory_list, False)
        self.on_directory_item_changed(None)

    def select_all_suffixes(self):
        self._set_all_checked(self.suffix_list, True)
        self.on_suffix_item_changed(None)

    def clear_suffixes(self):
        self._set_all_checked(self.suffix_list, False)
        self.on_suffix_item_changed(None)

    def update_scope_counts(self):
        checked_dirs = self._checked_values(self.directory_list)
        total_dirs = self._checkable_count(self.directory_list)
        self.dir_count_label.setText(
            I18n.get_text(
                "checked_dirs", self.lang,
                checked=len(checked_dirs), total=total_dirs,
            )
        )
        checked_suffixes = self._checked_values(self.suffix_list)
        total_suffixes = self._checkable_count(self.suffix_list)
        self.suffix_count_label.setText(
            I18n.get_text(
                "checked_suffixes", self.lang,
                checked=len(checked_suffixes), total=total_suffixes,
            )
        )
        if hasattr(self, "btn_start"):
            self.sync_ui_state()


    def change_mode(self):
        mode = self.mode_combo.currentData()
        if mode == self.scan_mode:
            return
        if self.is_scanning or self.is_running:
            index = self.mode_combo.findData(self.scan_mode)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
            return
        self.scan_mode = mode
        self.engine.set_scan_mode(mode)
        self.directory_frame.setVisible(mode == SCAN_MODE_LOCATION)
        self.suffix_frame.setVisible(mode == SCAN_MODE_SUFFIX)
        self._mark_scope_dirty()

    def change_theme_mode(self):
        mode = self.theme_combo.currentData()
        self.theme_mode = mode
        if mode == "system":
            self.theme_dark = system_is_dark()
        elif mode == "dark":
            self.theme_dark = True
        else:
            self.theme_dark = False
        self.sync_theme_polling()
        self.apply_theme(self.theme_dark)

    def manage_exclude_rules(self):
        dialog = ExcludeRulesDialog(self, self.exclude_patterns, self.lang)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.exclude_patterns = dialog.get_patterns()
            self.engine.set_ignore_patterns(self.exclude_patterns)
            self._mark_scope_dirty()

    def show_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        source_index = self.proxy.mapToSource(index)
        path = self.model.path_at_row(source_index.row())
        if not path:
            return
        menu = QMenu(self)
        open_action = menu.addAction(I18n.get_text("open_location", self.lang))
        copy_action = menu.addAction(I18n.get_text("copy_path", self.lang))
        exclude_action = menu.addAction(I18n.get_text("exclude_item", self.lang))
        clear_action = None
        if self.ignored_paths_raw:
            menu.addSeparator()
            clear_action = menu.addAction(
                I18n.get_text("clear_ignored", self.lang)
            )
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == open_action:
            target = path if os.path.isdir(path) else os.path.dirname(path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))
        elif action == copy_action:
            QApplication.clipboard().setText(path)
        elif action == exclude_action:
            self.ignored_paths_raw.add(os.path.normpath(path))
            self.engine.set_ignored_paths(self.ignored_paths_raw)
            self.add_log(I18n.get_text("excluded_item", self.lang, path=path), False)
            self._mark_scope_dirty()
        elif action == clear_action:
            self.clear_ignored_paths()

    def clear_ignored_paths(self):
        if not self.ignored_paths_raw:
            return
        self.ignored_paths_raw.clear()
        self.engine.set_ignored_paths(self.ignored_paths_raw)
        self.save_settings()
        self._mark_scope_dirty()

    def on_header_clicked(self, logicalIndex):
        if logicalIndex not in (0, 1, 2):
            return
        if self.sort_column == logicalIndex:
            self.sort_order = (
                Qt.SortOrder.DescendingOrder
                if self.sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self.sort_column = logicalIndex
            self.sort_order = Qt.SortOrder.AscendingOrder
        self.apply_sort()

    def apply_sort(self):
        if self.sort_column < 0:
            return
        self.proxy.sort(self.sort_column, self.sort_order)
        self.table.horizontalHeader().setSortIndicator(
            self.sort_column, self.sort_order
        )

    def apply_filter(self):
        self.proxy.set_path_filter(self.filter_input.text())

    def update_texts(self, refresh_table=False):
        t = lambda key: I18n.get_text(key, self.lang)
        self.setWindowTitle(t("title"))
        self.title_label.setText(t("title"))
        self.subtitle_label.setText(t("subtitle"))
        self.scan_mode_label.setText(t("scan_mode_label"))
        self.mode_combo.setItemText(0, t("mode_location"))
        self.mode_combo.setItemText(1, t("mode_suffix"))
        self.dir_scope_label.setText(t("dir_scope_label"))
        self.suffix_scope_label.setText(t("suffix_scope_label"))
        self.dir_intro_label.setText(t("dir_intro"))
        self.suffix_intro_label.setText(t("suffix_intro"))
        self.scan_root_label.setText(t("scan_root_label"))
        self.btn_pick_scan_root.setText(t("select_scan_dir"))
        self.scan_root_path.setText(self.scan_root)
        self.btn_select_all_dirs.setText(t("select_all_dirs"))
        self.btn_clear_dirs.setText(t("clear_dirs"))
        self.btn_select_all_suffixes.setText(t("select_all_suffixes"))
        self.btn_clear_suffixes.setText(t("clear_suffixes"))
        self.filter_input.setPlaceholderText(t("search"))
        self.overall_label.setText(t("overall_progress"))
        self.btn_refresh.setText(t("scan_now"))
        self.btn_stop_scan.setText(t("stop_scan"))
        self.btn_select_all.setText(t("select_all"))
        self.btn_deselect_all.setText(t("deselect_all"))
        self.btn_start.setText(t("start_clean"))
        self.btn_stop.setText(t("stop"))
        self.recycle_checkbox.setText(t("use_recycle"))
        self.btn_manage_rules.setText(t("manage_rules"))
        self.theme_label.setText(t("theme"))
        self.theme_combo.setItemText(0, t("system"))
        self.theme_combo.setItemText(1, t("dark"))
        self.theme_combo.setItemText(2, t("light"))
        self.model.set_language(self.lang)
        self.populate_directory_list()
        self.populate_suffix_list()
        self.update_scope_counts()
        if refresh_table:
            self.refresh_table_display()
        self.update_selected_count()
    def update_selected_count(self):
        if self.is_scanning or self.is_running:
            return
        count = self.model.selected_count()
        size_text = format_size(self.model.selected_size())
        self.status_bar.showMessage(
            I18n.get_text("selected_count", self.lang, count=count, size=size_text)
            + "  "
            + I18n.get_text("ready", self.lang)
        )

    def change_language(self, idx):
        self.lang = self.lang_combo.currentData()
        self.engine.lang = self.lang
        self.update_texts(refresh_table=True)

    def sync_ui_state(self):
        busy = self.is_scanning or self.is_running
        has_dirs = bool(self._checked_values(self.directory_list))
        has_suffixes = bool(self._checked_values(self.suffix_list))
        if self.scan_mode == SCAN_MODE_SUFFIX:
            scope_ready = has_suffixes and os.path.isdir(self.scan_root)
        else:
            scope_ready = has_dirs
        self.btn_refresh.setVisible(not busy)
        self.btn_stop_scan.setVisible(self.is_scanning and not self.is_running)
        self.btn_start.setEnabled(not busy and scope_ready and not self._scope_dirty)
        self.btn_stop.setVisible(self.is_running)
        self.btn_stop.setEnabled(self.is_running)
        self.btn_select_all.setEnabled(not self.is_running)
        self.btn_deselect_all.setEnabled(not self.is_running)
        self.mode_combo.setEnabled(not busy)
        self.directory_list.setEnabled(
            not busy and self.scan_mode == SCAN_MODE_LOCATION
        )
        self.suffix_list.setEnabled(
            not busy and self.scan_mode == SCAN_MODE_SUFFIX
        )
        self.btn_select_all_dirs.setEnabled(not busy)
        self.btn_clear_dirs.setEnabled(not busy)
        self.btn_select_all_suffixes.setEnabled(not busy)
        self.btn_clear_suffixes.setEnabled(not busy)
        self.btn_pick_scan_root.setEnabled(not busy)
        self.scan_root_path.setEnabled(not busy)
        self.recycle_checkbox.setEnabled(not busy)
        self.btn_manage_rules.setEnabled(not self.is_running)

    def start_scan(self):
        if self.is_running or self.is_scanning:
            return
        if self.scan_mode == SCAN_MODE_SUFFIX:
            scan_roots = [self.scan_root]
            if not scan_roots[0] or not os.path.isdir(scan_roots[0]):
                self.model.clear()
                self.sync_ui_state()
                self.show_message("info", I18n.get_text("no_scan_root_selected", self.lang))
                return
            suffix_tokens = self._checked_values(self.suffix_list)
            if not suffix_tokens:
                self.model.clear()
                self.sync_ui_state()
                self.show_message("info", I18n.get_text("no_suffix_selected", self.lang))
                return
            self.engine.set_selected_suffixes(suffix_tokens)
        else:
            scan_roots = self._checked_values(self.directory_list)
            if not scan_roots:
                self.model.clear()
                self.sync_ui_state()
                self.show_message("info", I18n.get_text("no_dirs_selected", self.lang))
                return
            self.selected_dirs = scan_roots
        self.engine.set_scan_roots(scan_roots)
        self.engine.set_ignored_paths(self.ignored_paths_raw)
        self.engine.set_ignore_patterns(self.exclude_patterns)
        self._scope_dirty = False
        self.is_scanning = True
        self.sync_ui_state()
        self.status_bar.showMessage(I18n.get_text("scanning", self.lang, count=0))
        self.model.clear()
        self.sort_column = -1
        self.sort_order = Qt.SortOrder.AscendingOrder
        self.proxy.sort(-1, Qt.SortOrder.AscendingOrder)
        self.engine.stop_event.clear()

        self.overall_progress.setRange(0, 0)
        self.overall_text.setText("")
        self.space_label.setText("")

        self.scan_start_time = time.time()
        self._last_status_update = 0.0
        self.scan_thread = ScanThread(self.engine)
        self.scan_thread.item_found.connect(self.on_item_found)
        self.scan_thread.finished_scan.connect(self.on_scan_finished)
        self.scan_thread.error_occurred.connect(self.on_scan_error)
        self.scan_thread.start()

    def stop_scan(self):
        if not self.is_scanning:
            return
        self.engine.stop()
        self.status_bar.showMessage(I18n.get_text("scan_stopped", self.lang))

    def on_item_found(self, item):
        try:
            mtime_text = (
                time.strftime("%Y-%m-%d %H:%M", time.localtime(item.mtime))
                if item.mtime
                else ""
            )
        except (OSError, ValueError):
            mtime_text = ""
        self.model.add_item(item.path, item.size, mtime_text)
        count = self.model.rowCount()
        now = time.monotonic()
        if (
            now - self._last_status_update >= STATUS_UPDATE_INTERVAL
            or count % TABLE_UPDATE_BATCH == 0
        ):
            self._last_status_update = now
            self.status_bar.showMessage(
                I18n.get_text("scanning", self.lang, count=count)
            )

    def _on_model_data_changed(self, top_left, bottom_right, roles):
        if roles and Qt.ItemDataRole.CheckStateRole not in roles:
            return
        self.update_selected_count()
        self.update_space_estimate()

    def update_space_estimate(self):
        count = self.model.selected_count()
        if not count:
            self.space_label.setText("")
            return
        total = self.model.selected_size()
        self.space_label.setText(
            I18n.get_text("space_usage", self.lang, size=format_size(total))
        )

    def refresh_table_display(self):
        self.update_selected_count()
        self.update_space_estimate()

    def on_scan_finished(self):
        self.is_scanning = False
        self.sync_ui_state()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        count = self.model.rowCount()
        self.overall_text.setText(f"0 / {count}")
        elapsed = time.time() - self.scan_start_time
        self.add_log(
            I18n.get_text("scan_stats", self.lang, count=count, elapsed=elapsed)
        )
        if self.engine.stop_event.is_set():
            self.status_bar.showMessage(I18n.get_text("scan_stopped", self.lang))
        elif count:
            self.update_selected_count()
        else:
            self.status_bar.showMessage(I18n.get_text("not_found", self.lang))
        if self.sort_column != -1:
            self.apply_sort()

    def on_scan_error(self, error_msg):
        self.is_scanning = False
        self.sync_ui_state()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        message = I18n.get_text("error_scan", self.lang, error=error_msg)
        self.show_message("error", message)
        self.status_bar.showMessage(message)

    def select_all(self):
        self.model.select_all()

    def deselect_all(self):
        self.model.clear_selection()
    def start_clean_with_confirm(self):
        if self.is_running:
            self.show_message("warning", I18n.get_text("clean_running", self.lang))
            return
        if self.is_scanning:
            self.show_message("warning", I18n.get_text("scan_running", self.lang))
            return
        if self.use_trash and not trash_available():
            self.show_message("warning", I18n.get_text("trash_unavailable", self.lang))
            return
        to_clean = []
        for path in self.model.selected_paths():
            if not os.path.lexists(path):
                continue
            if not self.engine.is_safe_path(path):
                continue
            to_clean.append(path)
        if not to_clean:
            self.show_message("info", I18n.get_text("no_item_selected", self.lang))
            return

        to_clean.sort(key=lambda path: self.model.size_at_path(path), reverse=True)
        preview_lines = []
        for path in to_clean[:MAX_CLEAN_PREVIEW]:
            preview_lines.append(
                f"{path}  ({format_size(self.model.size_at_path(path))})"
            )
        if len(to_clean) > MAX_CLEAN_PREVIEW:
            preview_lines.append(
                I18n.get_text(
                    "more_items", self.lang,
                    count=len(to_clean) - MAX_CLEAN_PREVIEW,
                )
            )
        preview = "\n".join(preview_lines)
        total_size = format_size(
            sum(self.model.size_at_path(path) for path in to_clean)
        )
        safe_text = (
            I18n.get_text("trash_note", self.lang)
            if self.use_trash
            else I18n.get_text("permanent_note", self.lang)
        )
        if self.scan_mode == SCAN_MODE_SUFFIX:
            template = I18n.get_text(
                "confirm_clean_suffix_text", self.lang,
                count=len(to_clean), size=total_size, safe_text=safe_text,
                list=preview,
            )
        else:
            template = I18n.get_text(
                "confirm_clean_location_text", self.lang,
                count=len(to_clean), size=total_size, safe_text=safe_text,
                list=preview,
            )
        msg = QMessageBox(self)
        msg.setWindowTitle(I18n.get_text("confirm_clean_title", self.lang))
        msg.setText(template)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return
        self.start_clean(to_clean)

    def start_clean(self, item_paths):
        self.is_running = True
        self.current_clean_paths = list(item_paths)
        self.sync_ui_state()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.overall_text.setText(f"0 / {len(item_paths)}")
        self.space_label.setText("")
        self.model.set_selectable(False)
        self.engine.stop_event.clear()
        self.clean_thread = DeleteThread(self.engine, item_paths, self.use_trash)
        self.clean_thread.log_signal.connect(self.add_log)
        self.clean_thread.progress_signal.connect(self.update_progress)
        self.clean_thread.finished_signal.connect(self.on_clean_finished)
        self.clean_thread.error_signal.connect(self.on_clean_error)
        self.clean_thread.start()

    def stop_clean(self):
        if not self.is_running:
            return
        self.engine.stop()
        self.btn_stop.setEnabled(False)
        self.status_bar.showMessage(I18n.get_text("clean_stopped", self.lang))

    def on_clean_finished(self, failed_list, remaining, deleted_paths):
        self.finalize_clean(failed_list, remaining, deleted_paths)

    def finalize_clean(self, failed_list, remaining, deleted_paths):
        self.is_running = False
        self.sync_ui_state()
        self.model.remove_paths(deleted_paths)
        for path in failed_list:
            self.model.update_status(path, CacheTableModel.STATUS_FAILED)
        self.model.clear_selection()
        self.model.set_selectable(True)
        self.refresh_table_display()

        cleaned_count = len(deleted_paths)
        failed_count = len(failed_list)
        if remaining:
            self.status_bar.showMessage(I18n.get_text("clean_stopped", self.lang))
        elif failed_count:
            self.status_bar.showMessage(
                I18n.get_text(
                    "clean_summary", self.lang,
                    cleaned=cleaned_count, failed=failed_count,
                )
            )
        else:
            self.status_bar.showMessage(I18n.get_text("all_done", self.lang))
        if failed_count:
            self.show_message(
                "warning",
                I18n.get_text(
                    "clean_summary", self.lang,
                    cleaned=cleaned_count, failed=failed_count,
                ),
            )

    def on_clean_error(self, error_msg):
        self.show_message("error", error_msg)
        self.finalize_clean(
            list(getattr(self, "current_clean_paths", [])), [], []
        )

    def add_log(self, message, error=False):
        color = "red" if error else "inherit"
        safe_message = html.escape(str(message))
        self.log_text.appendHtml(
            f'<span style="color:{color};">'
            f'[{time.strftime("%H:%M:%S")}] {safe_message}</span>'
        )

    def update_progress(self, completed, total):
        if total > 0:
            self.overall_progress.setValue(int(completed / total * 100))
            self.overall_text.setText(f"{completed} / {total}")
        else:
            self.overall_progress.setValue(0)
            self.overall_text.setText("0 / 0")

    def show_message(self, icon_type, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(I18n.get_text("dialog_" + icon_type, self.lang))
        msg.setText(text)
        if icon_type == "info":
            msg.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        else:
            msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()

    def apply_theme(self, dark):
        _apply_theme(self, dark)
