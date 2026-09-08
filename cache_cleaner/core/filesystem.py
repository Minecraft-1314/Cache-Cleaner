"""Filesystem helpers shared by the scanner and the UI."""

import ctypes
import ctypes.wintypes
import os
import shutil
import stat
import sys

try:
    import send2trash
    _SEND2TRASH_AVAILABLE = True
except ImportError:
    _SEND2TRASH_AVAILABLE = False

_FO_DELETE = 3
_FOF_ALLOWUNDO = 0x40
_FOF_NOCONFIRMATION = 0x10
_FOF_SILENT = 0x4
_FOF_NOERRORUI = 0x400


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.wintypes.HWND),
        ("wFunc", ctypes.c_uint),
        ("pFrom", ctypes.c_wchar_p),
        ("pTo", ctypes.c_wchar_p),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", ctypes.c_int),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", ctypes.c_wchar_p),
    ]


def trash_available():
    return _SEND2TRASH_AVAILABLE or sys.platform == "win32"


def _move_to_trash_windows(path):
    source_buffer = ctypes.create_unicode_buffer(os.path.abspath(path) + "\0")
    operation = _SHFILEOPSTRUCTW(
        hwnd=None,
        wFunc=_FO_DELETE,
        pFrom=ctypes.cast(source_buffer, ctypes.c_wchar_p),
        pTo=None,
        fFlags=_FOF_ALLOWUNDO | _FOF_NOCONFIRMATION | _FOF_SILENT | _FOF_NOERRORUI,
        fAnyOperationsAborted=0,
        hNameMappings=None,
        lpszProgressTitle=None,
    )
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if result:
        raise OSError(f"SHFileOperationW returned {result}")


def format_size(size):
    try:
        value = float(size or 0)
    except (TypeError, ValueError):
        value = 0.0
    units = (("B", 0), ("KB", 1), ("MB", 1), ("GB", 2), ("TB", 2))
    for unit, digits in units:
        if value < 1024 or unit == units[-1][0]:
            return f"{value:.{digits}f} {unit}"
        value /= 1024


def get_path_size(path, stop_event=None):
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    pending = [path]
    while pending:
        if stop_event is not None and stop_event.is_set():
            return total
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if stop_event is not None and stop_event.is_set():
                        return total
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            pending.append(entry.path)
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def _clear_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass
    func(path)


def delete_path(path, use_trash=False):
    try:
        if use_trash:
            if _SEND2TRASH_AVAILABLE:
                send2trash.send2trash(path)
                return True, ""
            if sys.platform == "win32":
                _move_to_trash_windows(path)
                return True, ""
            return False, "trash_unavailable"
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, onerror=_clear_readonly)
        elif os.path.islink(path) or os.path.isfile(path):
            try:
                os.remove(path)
            except PermissionError:
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
        elif os.path.exists(path):
            return False, "path_missing"
        return True, ""
    except PermissionError:
        return False, "permission_denied"
    except OSError as exc:
        return False, str(exc)
