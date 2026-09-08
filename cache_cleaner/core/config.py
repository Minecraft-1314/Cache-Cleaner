"""Application constants and system locale resolution."""

import locale
import os

APP_ORG = "CacheCleaner"
APP_NAME = "CacheCleaner"
DEFAULT_CLUSTER_SIZE = 4096
MAX_RECENT_DIRS = 8
MAX_CLEAN_PREVIEW = 20
LOG_MAX_BLOCKS = 500
THEME_POLL_INTERVAL_MS = 2000
THREAD_QUIT_TIMEOUT_MS = 5000
TABLE_UPDATE_BATCH = 100
STATUS_UPDATE_INTERVAL = 0.25
SCAN_DIRECT_MAX_WORKERS = 4
SCAN_MODE_LOCATION = "location"
SCAN_MODE_SUFFIX = "suffix"
MIN_WINDOW_WIDTH = 1040
MIN_WINDOW_HEIGHT = 680
FONT_FAMILY = "Segoe UI"
LANG_COMBO_WIDTH = 110
TABLE_SIZE_WIDTH = 110
TABLE_TIME_WIDTH = 150
TABLE_STATUS_WIDTH = 130
TABLE_SELECT_WIDTH = 80
IGNORE_DIALOG_MIN_WIDTH = 420

def get_system_language():
    try:
        locale.setlocale(locale.LC_ALL, "")
        code, _ = locale.getlocale()
    except Exception:
        code = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    return "zh" if code and code.lower().startswith("zh") else "en"
