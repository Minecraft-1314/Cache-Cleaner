"""Background scan and clean workers for cache items."""

import fnmatch
import os
import queue
import sys
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from .config import SCAN_DIRECT_MAX_WORKERS, SCAN_MODE_LOCATION, SCAN_MODE_SUFFIX
from .filesystem import delete_path, get_path_size, trash_available
from .i18n import I18n
from .suffixes import get_suffix_rules


@dataclass(frozen=True)
class CacheItem:
    path: str
    is_dir: bool
    size: int
    mtime: float
    root: str


class CacheScanEngine:
    def __init__(self, scan_roots, scan_mode, lang="en"):
        self.scan_roots = []
        self.scan_mode = scan_mode
        self.lang = lang
        self.suffix_rules = {rule.token: rule for rule in get_suffix_rules()}
        self.selected_suffixes = set()
        self.stop_event = threading.Event()
        self.ignored_paths = set()
        self.ignore_patterns = []
        self.case_insensitive = sys.platform == "win32"
        self.set_scan_roots(scan_roots)

    def _t(self, key, **kwargs):
        return I18n.get_text(key, self.lang, **kwargs)

    def set_scan_roots(self, roots):
        normalized = []
        for path in roots or []:
            norm = os.path.normcase(os.path.normpath(path))
            if not norm or norm in {r[0] for r in normalized}:
                continue
            if not any(self._is_within(norm, kept) for kept, _ in normalized):
                normalized.append((norm, os.path.normpath(path)))
        self.scan_roots = [path for _, path in sorted(
            normalized, key=lambda item: os.path.normpath(item[1]).count(os.sep)
        )]

    def set_scan_mode(self, mode):
        self.scan_mode = mode

    def set_selected_suffixes(self, tokens):
        self.selected_suffixes = {
            token for token in tokens if token in self.suffix_rules
        }

    def set_ignored_paths(self, paths):
        normalized = {os.path.normpath(p) for p in paths}
        self.ignored_paths = (
            {p.lower() for p in normalized} if self.case_insensitive else normalized
        )

    def set_ignore_patterns(self, patterns):
        self.ignore_patterns = patterns

    @staticmethod
    def _is_within(candidate, root):
        candidate = os.path.normcase(os.path.normpath(candidate))
        root = os.path.normcase(os.path.normpath(root))
        if candidate == root:
            return False
        try:
            return os.path.commonpath([root, candidate]) == root
        except ValueError:
            return False

    def _ignored_name(self, name):
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def _ignored_path(self, path):
        norm = os.path.normpath(path)
        candidate = norm.lower() if self.case_insensitive else norm
        return candidate in self.ignored_paths or self._ignored_name(os.path.basename(norm))

    def is_safe_path(self, path):
        if not path:
            return False
        norm = os.path.normpath(path)
        if self.scan_mode == SCAN_MODE_LOCATION:
            parent = os.path.dirname(norm)
            for root in self.scan_roots:
                if os.path.normcase(os.path.normpath(parent)) == os.path.normcase(os.path.normpath(root)):
                    return True
            return False
        return any(
            self._is_within(norm, root) and norm != os.path.normpath(root)
            for root in self.scan_roots
        )

    def scan_cache_items(self):
        if not self.scan_roots:
            return
        if self.scan_mode == SCAN_MODE_SUFFIX:
            yield from self._scan_suffix_items()
        else:
            yield from self._scan_location_items()

    def _scan_location_items(self):
        for root in self.scan_roots:
            if not os.path.isdir(root):
                continue
            yield from self._scan_location_root(root)

    def _scan_location_root(self, root):
        entries = []
        try:
            with os.scandir(root) as iterator:
                for entry in iterator:
                    try:
                        is_file = entry.is_file(follow_symlinks=False)
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_file or is_dir:
                        entries.append((entry.name, entry.path, is_dir))
        except OSError:
            return
        entries.sort(key=lambda item: item[0])
        if not entries:
            return

        result_queue = queue.Queue()

        def analyze(entry):
            name, path, is_dir = entry
            try:
                if self.stop_event.is_set() or self._ignored_path(path):
                    result_queue.put(None)
                    return
                if is_dir:
                    size = get_path_size(path, self.stop_event)
                else:
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        size = 0
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    mtime = 0.0
                result_queue.put(
                    CacheItem(
                        path=path, is_dir=is_dir, size=size,
                        mtime=mtime, root=root,
                    )
                )
            except Exception:
                result_queue.put(None)

        workers = max(1, min(SCAN_DIRECT_MAX_WORKERS, len(entries)))
        executor = ThreadPoolExecutor(max_workers=workers)
        futures = [executor.submit(analyze, entry) for entry in entries]
        pending = len(futures)
        try:
            while pending:
                if self.stop_event.is_set():
                    for future in futures:
                        future.cancel()
                    break
                item = result_queue.get()
                pending -= 1
                if item is None:
                    continue
                yield item
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

    def _selected_rule_tokens(self):
        return [
            rule for token, rule in self.suffix_rules.items()
            if token in self.selected_suffixes
        ]

    def _matches_rule(self, name, rule):
        lowered = name.lower()
        if rule.kind == "name":
            return lowered == rule.token.lower()
        if rule.kind == "ends":
            return lowered.endswith(rule.token.lower())
        return os.path.splitext(name)[1].lower() == rule.token.lower()

    def _scan_suffix_items(self):
        rules = self._selected_rule_tokens()
        if not rules:
            return
        for root in self.scan_roots:
            if not os.path.isdir(root):
                continue
            yield from self._scan_suffix_root(root, rules)

    def _scan_suffix_root(self, root, rules):
        try:
            walker = os.walk(
                root,
                topdown=True,
                onerror=lambda error: None,
                followlinks=False,
            )
            for current, dirs, files in walker:
                if self.stop_event.is_set():
                    return
                dirs[:] = sorted(d for d in dirs if not self._ignored_name(d))
                for name in sorted(files):
                    if self.stop_event.is_set():
                        return
                    path = os.path.join(current, name)
                    if self._ignored_path(path) or os.path.islink(path):
                        continue
                    if not any(self._matches_rule(name, rule) for rule in rules):
                        continue
                    try:
                        stat_result = os.stat(path)
                    except OSError:
                        continue
                    yield CacheItem(
                        path=path,
                        is_dir=False,
                        size=stat_result.st_size,
                        mtime=stat_result.st_mtime,
                        root=root,
                    )
        except OSError:
            return

    @staticmethod
    def _path_depth(path):
        return os.path.normpath(path).count(os.sep)

    def delete_items(self, paths, log_signal, progress_signal, use_trash=False):
        if use_trash and not trash_available():
            log_signal.emit(self._t("trash_unavailable"), True)
            progress_signal.emit(0, 0)
            return list(paths), [], []

        safe_paths = [path for path in paths if self.is_safe_path(path)]
        if len(safe_paths) != len(paths):
            log_signal.emit(self._t("outside_scan_root"), True)

        ordered = sorted(
            set(safe_paths),
            key=lambda path: (self._path_depth(path), path),
            reverse=True,
        )
        pending = deque(ordered)
        completed = 0
        total = len(pending)
        failed = []
        deleted = []
        remaining = []

        while pending:
            if self.stop_event.is_set():
                remaining.extend(pending)
                log_signal.emit(self._t("clean_stopped"), False)
                break
            path = pending.popleft()
            log_signal.emit(self._t("cleaning", path=path), False)
            if not os.path.lexists(path):
                log_signal.emit(self._t("clean_missing", path=path), False)
                deleted.append(path)
                completed += 1
                progress_signal.emit(completed, total)
                continue
            ok, error_key = delete_path(path, use_trash=use_trash)
            if ok:
                log_signal.emit(
                    self._t(
                        "cleaned_trash_msg" if use_trash else "cleaned_msg",
                        path=path,
                    ),
                    False,
                )
                deleted.append(path)
            else:
                if error_key == "permission_denied":
                    log_signal.emit(self._t("permission_denied", path=path), True)
                elif error_key == "trash_unavailable":
                    log_signal.emit(self._t("trash_unavailable"), True)
                else:
                    log_signal.emit(
                        self._t("clean_error", path=path, error=error_key), True
                    )
                failed.append(path)
            completed += 1
            progress_signal.emit(completed, total)

        if not remaining and not failed:
            log_signal.emit(self._t("all_done"), False)
        progress_signal.emit(0, 0)
        return failed, remaining, deleted

    def stop(self):
        self.stop_event.set()


class ScanThread(QThread):
    item_found = pyqtSignal(object)
    finished_scan = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            for item in self.engine.scan_cache_items():
                self.item_found.emit(item)
            self.finished_scan.emit()
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class DeleteThread(QThread):
    log_signal = pyqtSignal(str, bool)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(list, list, list)
    error_signal = pyqtSignal(str)

    def __init__(self, engine, item_paths, use_trash):
        super().__init__()
        self.engine = engine
        self.item_paths = item_paths
        self.use_trash = use_trash

    def run(self):
        try:
            failed, remaining, deleted = self.engine.delete_items(
                self.item_paths,
                self.log_signal,
                self.progress_signal,
                use_trash=self.use_trash,
            )
            self.finished_signal.emit(failed, remaining, deleted)
        except Exception as exc:
            self.error_signal.emit(str(exc))
