"""Factories that assemble the main window sections."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QPlainTextEdit, QProgressBar,
    QPushButton, QSplitter, QTableView, QVBoxLayout, QWidget
)

from ..core.config import (
    FONT_FAMILY, LANG_COMBO_WIDTH, LOG_MAX_BLOCKS, SCAN_MODE_LOCATION,
    SCAN_MODE_SUFFIX, TABLE_SELECT_WIDTH, TABLE_SIZE_WIDTH, TABLE_STATUS_WIDTH,
    TABLE_TIME_WIDTH, TABLE_SELECT_COLUMN
)
from ..core.i18n import I18n
from .table_model import CacheProxyModel, CacheTableModel, CheckStateDelegate


def _heading_font(size, weight=QFont.Weight.Normal):
    return QFont(FONT_FAMILY, size, weight)


def build_header(window, content_layout):
    header_layout = QHBoxLayout()
    window.title_label = QLabel()
    window.title_label.setFont(_heading_font(24, QFont.Weight.Bold))
    header_layout.addWidget(window.title_label)
    header_layout.addStretch()

    controls_layout = QHBoxLayout()
    theme_layout = QHBoxLayout()
    theme_label = QLabel(I18n.get_text("theme", window.lang))
    window.theme_label = theme_label
    window.theme_combo = QComboBox()
    window.theme_combo.addItem(I18n.get_text("system", window.lang), "system")
    window.theme_combo.addItem(I18n.get_text("dark", window.lang), "dark")
    window.theme_combo.addItem(I18n.get_text("light", window.lang), "light")
    idx = window.theme_combo.findData(window.theme_mode)
    window.theme_combo.setCurrentIndex(idx if idx >= 0 else 0)
    window.theme_combo.currentIndexChanged.connect(window.change_theme_mode)
    theme_layout.addWidget(theme_label)
    theme_layout.addWidget(window.theme_combo)
    controls_layout.addLayout(theme_layout)

    window.lang_combo = QComboBox()
    window.lang_combo.addItem("English", "en")
    window.lang_combo.addItem("中文", "zh")
    window.lang_combo.setCurrentIndex(0 if window.lang == "en" else 1)
    window.lang_combo.currentIndexChanged.connect(window.change_language)
    window.lang_combo.setFixedWidth(LANG_COMBO_WIDTH)
    controls_layout.addWidget(window.lang_combo)

    header_layout.addLayout(controls_layout)
    content_layout.addLayout(header_layout)


def build_scan_bar(window, content_layout):
    row_layout = QHBoxLayout()
    window.scan_mode_label = QLabel(I18n.get_text("scan_mode_label", window.lang))
    window.mode_combo = QComboBox()
    window.mode_combo.addItem(
        I18n.get_text("mode_location", window.lang), SCAN_MODE_LOCATION
    )
    window.mode_combo.addItem(
        I18n.get_text("mode_suffix", window.lang), SCAN_MODE_SUFFIX
    )
    mode_idx = window.mode_combo.findData(window.scan_mode)
    window.mode_combo.setCurrentIndex(mode_idx if mode_idx >= 0 else 0)
    window.mode_combo.currentIndexChanged.connect(window.change_mode)
    row_layout.addWidget(window.scan_mode_label)
    row_layout.addWidget(window.mode_combo)
    row_layout.addStretch()
    content_layout.addLayout(row_layout)


def _scope_buttons(window, all_key, clear_key, all_callback, clear_callback):
    select_all_btn = QPushButton(I18n.get_text(all_key, window.lang))
    select_all_btn.clicked.connect(all_callback)
    clear_btn = QPushButton(I18n.get_text(clear_key, window.lang))
    clear_btn.clicked.connect(clear_callback)
    return select_all_btn, clear_btn


def build_scope_panel(window, content_layout):
    scope_layout = QHBoxLayout()

    dir_frame = QFrame()
    dir_frame.setFrameShape(QFrame.Shape.StyledPanel)
    dir_layout = QVBoxLayout(dir_frame)
    dir_layout.setContentsMargins(8, 6, 8, 6)
    window.dir_scope_label = QLabel(I18n.get_text("dir_scope_label", window.lang))
    window.dir_scope_label.setFont(_heading_font(10, QFont.Weight.Bold))
    window.dir_count_label = QLabel()
    header = QHBoxLayout()
    header.addWidget(window.dir_scope_label)
    header.addStretch()
    header.addWidget(window.dir_count_label)
    dir_layout.addLayout(header)
    window.dir_intro_label = QLabel(I18n.get_text("dir_intro", window.lang))
    window.dir_intro_label.setWordWrap(True)
    dir_layout.addWidget(window.dir_intro_label)

    window.directory_list = QListWidget()
    window.directory_list.setMinimumHeight(150)
    dir_layout.addWidget(window.directory_list, 1)

    dir_buttons = QHBoxLayout()
    window.btn_select_all_dirs, window.btn_clear_dirs = _scope_buttons(
        window, "select_all_dirs", "clear_dirs",
        window.select_all_directories, window.clear_directories,
    )
    dir_buttons.addWidget(window.btn_select_all_dirs)
    dir_buttons.addWidget(window.btn_clear_dirs)
    dir_buttons.addStretch()
    dir_layout.addLayout(dir_buttons)

    suffix_frame = QFrame()
    suffix_frame.setFrameShape(QFrame.Shape.StyledPanel)
    suffix_layout = QVBoxLayout(suffix_frame)
    suffix_layout.setContentsMargins(8, 6, 8, 6)
    window.suffix_scope_label = QLabel(
        I18n.get_text("suffix_scope_label", window.lang)
    )
    window.suffix_scope_label.setFont(_heading_font(10, QFont.Weight.Bold))
    window.suffix_count_label = QLabel()
    suffix_header = QHBoxLayout()
    suffix_header.addWidget(window.suffix_scope_label)
    suffix_header.addStretch()
    suffix_header.addWidget(window.suffix_count_label)
    suffix_layout.addLayout(suffix_header)
    window.suffix_intro_label = QLabel(I18n.get_text("suffix_intro", window.lang))
    window.suffix_intro_label.setWordWrap(True)
    suffix_layout.addWidget(window.suffix_intro_label)

    scan_root_row = QHBoxLayout()
    window.scan_root_label = QLabel(I18n.get_text("scan_root_label", window.lang))
    window.scan_root_path = QLineEdit()
    window.scan_root_path.setReadOnly(True)
    window.btn_pick_scan_root = QPushButton(
        I18n.get_text("select_scan_dir", window.lang)
    )
    window.btn_pick_scan_root.clicked.connect(window.pick_scan_root)
    scan_root_row.addWidget(window.scan_root_label)
    scan_root_row.addWidget(window.scan_root_path, 1)
    scan_root_row.addWidget(window.btn_pick_scan_root)
    suffix_layout.addLayout(scan_root_row)

    window.suffix_list = QListWidget()
    window.suffix_list.setMinimumHeight(150)
    suffix_layout.addWidget(window.suffix_list, 1)

    suffix_buttons = QHBoxLayout()
    window.btn_select_all_suffixes, window.btn_clear_suffixes = _scope_buttons(
        window, "select_all_suffixes", "clear_suffixes",
        window.select_all_suffixes, window.clear_suffixes,
    )
    suffix_buttons.addWidget(window.btn_select_all_suffixes)
    suffix_buttons.addWidget(window.btn_clear_suffixes)
    suffix_buttons.addStretch()
    suffix_layout.addLayout(suffix_buttons)

    scope_layout.addWidget(dir_frame, 1)
    scope_layout.addWidget(suffix_frame, 1)
    content_layout.addLayout(scope_layout)
    window.directory_frame = dir_frame
    window.suffix_frame = suffix_frame


def build_filter_bar(window, content_layout):
    filter_layout = QHBoxLayout()
    window.filter_input = QLineEdit()
    window.filter_input.setPlaceholderText(I18n.get_text("search", window.lang))
    window.filter_input.textChanged.connect(window.apply_filter)
    filter_layout.addWidget(window.filter_input, 1)
    window.btn_manage_rules = QPushButton(
        I18n.get_text("manage_rules", window.lang)
    )
    window.btn_manage_rules.clicked.connect(window.manage_exclude_rules)
    filter_layout.addWidget(window.btn_manage_rules)
    content_layout.addLayout(filter_layout)


def build_result_area(window, content_layout):
    window.splitter = QSplitter(Qt.Orientation.Vertical)

    table_container = QFrame()
    table_container.setFrameShape(QFrame.Shape.StyledPanel)
    table_layout = QVBoxLayout(table_container)
    table_layout.setContentsMargins(0, 0, 0, 0)

    window.model = CacheTableModel(window.lang, window)
    window.proxy = CacheProxyModel(window)
    window.proxy.setSourceModel(window.model)
    window.table = QTableView()
    window.table.setModel(window.proxy)
    window.table.setItemDelegate(
        CheckStateDelegate(TABLE_SELECT_COLUMN, window.table)
    )
    header = window.table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(1, TABLE_SIZE_WIDTH)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(2, TABLE_TIME_WIDTH)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(3, TABLE_STATUS_WIDTH)
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
    header.resizeSection(4, TABLE_SELECT_WIDTH)
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(True)
    window.table.verticalHeader().setVisible(False)
    window.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    window.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    window.table.setAlternatingRowColors(False)
    window.table.setSortingEnabled(False)
    window.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window.table.customContextMenuRequested.connect(window.show_context_menu)
    header.sectionClicked.connect(window.on_header_clicked)
    table_layout.addWidget(window.table)

    log_container = QFrame()
    log_container.setFrameShape(QFrame.Shape.StyledPanel)
    log_layout = QVBoxLayout(log_container)
    log_layout.setContentsMargins(0, 0, 0, 0)
    window.log_text = QPlainTextEdit()
    window.log_text.setReadOnly(True)
    window.log_text.setMaximumBlockCount(LOG_MAX_BLOCKS)
    window.log_text.setFrameShape(QFrame.Shape.NoFrame)
    log_layout.addWidget(window.log_text)

    window.splitter.addWidget(table_container)
    window.splitter.addWidget(log_container)
    window.splitter.setStretchFactor(0, 2)
    window.splitter.setStretchFactor(1, 1)
    content_layout.addWidget(window.splitter, 1)


def build_progress_area(window, content_layout):
    progress_layout = QVBoxLayout()
    window.overall_label = QLabel()
    window.overall_label.setFont(_heading_font(10, QFont.Weight.Bold))
    progress_layout.addWidget(window.overall_label)
    overall_row = QHBoxLayout()
    window.overall_progress = QProgressBar()
    window.overall_progress.setRange(0, 100)
    overall_row.addWidget(window.overall_progress, 1)
    window.overall_text = QLabel("0 / 0")
    overall_row.addWidget(window.overall_text)
    progress_layout.addLayout(overall_row)
    window.space_label = QLabel()
    progress_layout.addWidget(window.space_label)
    content_layout.addLayout(progress_layout)


def build_action_bar(window, content_layout):
    button_layout = QHBoxLayout()
    window.btn_refresh = QPushButton()
    window.btn_refresh.clicked.connect(window.start_scan)
    window.btn_stop_scan = QPushButton()
    window.btn_stop_scan.clicked.connect(window.stop_scan)
    window.btn_stop_scan.setVisible(False)
    window.btn_select_all = QPushButton()
    window.btn_select_all.clicked.connect(window.select_all)
    window.btn_deselect_all = QPushButton()
    window.btn_deselect_all.clicked.connect(window.deselect_all)
    button_layout.addWidget(window.btn_refresh)
    button_layout.addWidget(window.btn_stop_scan)
    button_layout.addWidget(window.btn_select_all)
    button_layout.addWidget(window.btn_deselect_all)

    window.recycle_checkbox = QCheckBox(I18n.get_text("use_recycle", window.lang))
    window.recycle_checkbox.setChecked(window.use_trash)
    window.recycle_checkbox.stateChanged.connect(
        lambda state: setattr(window, "use_trash", state == Qt.CheckState.Checked.value)
    )
    button_layout.addWidget(window.recycle_checkbox)

    button_layout.addStretch()

    window.btn_start = QPushButton()
    window.btn_start.clicked.connect(window.start_clean_with_confirm)
    window.btn_stop = QPushButton()
    window.btn_stop.clicked.connect(window.stop_clean)
    window.btn_stop.setEnabled(False)
    button_layout.addWidget(window.btn_start)
    button_layout.addWidget(window.btn_stop)
    content_layout.addLayout(button_layout)


def build_ui(window):
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(18, 12, 18, 12)
    content_layout.setSpacing(10)

    build_header(window, content_layout)
    window.subtitle_label = QLabel()
    window.subtitle_label.setFont(_heading_font(10))
    content_layout.addWidget(window.subtitle_label)
    build_scan_bar(window, content_layout)
    build_scope_panel(window, content_layout)
    build_filter_bar(window, content_layout)
    build_result_area(window, content_layout)
    build_progress_area(window, content_layout)
    build_action_bar(window, content_layout)

    main_layout.addWidget(content_widget, 1)
