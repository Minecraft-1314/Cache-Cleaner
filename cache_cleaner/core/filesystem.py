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
_TRASH_FLAG_MASK = _FOF_ALLOWUNDO | _FOF_NOCONFIRMATION | _FOF_SILENT | _FOF_NOERRORUI
_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")
_BYTE_ROUNDING_LIMIT = 1023.5
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_REMOVAL_CALLS = frozenset({"unlink", "rmdir", "remove"})


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
        fFlags=_TRASH_FLAG_MASK,
        fAnyOperationsAborted=0,
        hNameMappings=None,
        lpszProgressTitle=None,
    )
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if result or operation.fAnyOperationsAborted:
        raise OSError(f"SHFileOperationW returned {result}")
    if os.path.lexists(path):
        raise OSError("item still present after move to Recycle Bin")


def format_size(size):
    try:
        value = max(float(size or 0), 0.0)
    except (TypeError, ValueError):
        value = 0.0
    index = 0
    while value >= 1024 and index < len(_SIZE_UNITS) - 1:
        value /= 1024
        index += 1
    if index == 0 and value >= _BYTE_ROUNDING_LIMIT:
        return f"{value / 1024:.2f} {_SIZE_UNITS[1]}"
    digits = 0 if index == 0 else 2
    return f"{value:.{digits}f} {_SIZE_UNITS[index]}"


def get_path_size(path, stop_event=None):
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    if _is_reparse_point(path):
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
                        if entry.is_symlink() or _is_reparse_point(entry.path):
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
    if getattr(func, "__name__", "") not in _REMOVAL_CALLS:
        raise exc_info[1]
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass
    func(path)


def _is_reparse_point(path):
    if sys.platform != "win32":
        return False
    try:
        attributes = os.lstat(path).st_file_attributes
    except (OSError, AttributeError, ValueError):
        return False
    return bool(attributes & _REPARSE_POINT)


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
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path) and _is_reparse_point(path):
            os.rmdir(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, onerror=_clear_readonly)
        elif os.path.isfile(path):
            try:
                os.remove(path)
            except PermissionError:
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
        elif os.path.exists(path):
            return False, "path_missing"
        if os.path.lexists(path):
            return False, "delete_incomplete"
        return True, ""
    except PermissionError:
        return False, "permission_denied"
    except OSError as exc:
        return False, str(exc)
