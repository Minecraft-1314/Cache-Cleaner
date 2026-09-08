"""Full built-in cache directory catalog."""

import os
import sys
import tempfile
from dataclasses import dataclass


LOCATION_GROUPS = ("system", "browser", "dev", "app")


@dataclass(frozen=True)
class CacheLocation:
    key: str
    label_zh: str
    label_en: str
    path: str
    group: str = "system"
    admin: bool = False
    warning: bool = False

    def label(self, lang):
        text = self.label_zh if lang == "zh" else self.label_en
        if self.admin:
            text += "（需管理员）" if lang == "zh" else " (admin)"
        if self.warning:
            text += "（谨慎）" if lang == "zh" else " (caution)"
        return text


def _base_dirs():
    home = os.path.expanduser("~")
    local = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    roaming = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
    program_data = os.environ.get("ProgramData") or r"C:\ProgramData"
    windows_dir = os.environ.get("SystemRoot") or r"C:\Windows"
    return home, local, roaming, program_data, windows_dir


def _pick(windows_path, unix_path):
    return windows_path if sys.platform == "win32" else unix_path


def _profile_names(user_data):
    try:
        names = sorted(
            entry.name
            for entry in os.scandir(user_data)
            if entry.is_dir() and (entry.name == "Default" or entry.name.startswith("Profile "))
        )
    except OSError:
        return []
    return names or ["Default"]




def get_cache_locations():
    home, local, roaming, program_data, windows_dir = _base_dirs()
    locations = []

    locations.extend([
        CacheLocation(
            "user_temp", "用户临时文件", "User Temp Files",
            tempfile.gettempdir(), "system",
        ),
        CacheLocation(
            "dot_cache", "用户缓存目录", "User Cache Directory",
            _pick(os.path.join(home, ".cache"), os.path.join(home, ".cache")),
            "system",
        ),
    ])

    if sys.platform == "win32":
        locations.extend([
            CacheLocation(
                "win_system_temp", "Windows 系统临时目录", "Windows System Temp",
                os.path.join(windows_dir, "Temp"), "system", True,
            ),
            CacheLocation(
                "win_update_download", "Windows 更新下载缓存", "Windows Update Download Cache",
                os.path.join(windows_dir, "SoftwareDistribution", "Download"),
                "system", True,
            ),
            CacheLocation(
                "win_prefetch", "Windows 预读取", "Windows Prefetch",
                os.path.join(windows_dir, "Prefetch"), "system", True,
            ),
            CacheLocation(
                "win_thumbnails", "Windows 缩略图缓存", "Windows Thumbnail Cache",
                os.path.join(local, "Microsoft", "Windows", "Explorer"), "system",
            ),
            CacheLocation(
                "win_search_index", "Windows 搜索索引", "Windows Search Index",
                os.path.join(program_data, "Microsoft", "Search", "Data", "Applications", "Windows"),
                "system", True, True,
            ),
            CacheLocation(
                "win_inet_cache", "Windows Internet 临时缓存", "Windows INetCache",
                os.path.join(local, "Microsoft", "Windows", "INetCache"), "system",
            ),
            CacheLocation(
                "win_webcache", "Windows WebCache", "Windows WebCache",
                os.path.join(local, "Microsoft", "Windows", "WebCache"),
                "system", False, True,
            ),
            CacheLocation(
                "win_wer", "Windows 错误报告缓存", "Windows Error Reporting Cache",
                os.path.join(local, "Microsoft", "Windows", "WER"),
                "system", False, True,
            ),
            CacheLocation(
                "win_crash_dumps", "应用程序崩溃转储", "Application Crash Dumps",
                os.path.join(local, "CrashDumps"), "system",
            ),
            CacheLocation(
                "win_update_datastore", "Windows 更新数据存储", "Windows Update Data Store",
                os.path.join(windows_dir, "SoftwareDistribution", "DataStore"),
                "system", True, True,
            ),
            CacheLocation(
                "win_delivery_opt", "Windows 传递优化缓存", "Windows Delivery Optimization Cache",
                os.path.join(
                    windows_dir, "ServiceProfiles", "NetworkService", "AppData",
                    "Local", "Microsoft", "Windows", "DeliveryOptimization", "Cache",
                ),
                "system", True,
            ),
            CacheLocation(
                "installer_package_cache", "安装程序包缓存", "Installer Package Cache",
                os.path.join(program_data, "Package Cache"),
                "system", False, True,
            ),
        ])
    else:
        cache_home = os.path.join(home, ".cache")
        if sys.platform == "darwin":
            cache_home = os.path.join(home, "Library", "Caches")
        locations.extend([
            CacheLocation(
                "system_cache", "系统级缓存", "System Cache",
                "/Library/Caches" if sys.platform == "darwin" else "/var/cache",
                "system", True,
            ),
            CacheLocation(
                "system_temp", "系统临时目录", "System Temp Directory",
                _pick("/tmp", "/var/tmp") if sys.platform != "darwin" else "/private/var/folders",
                "system", True,
            ),
            CacheLocation(
                "font_cache", "字体缓存", "Font Cache",
                os.path.join(cache_home, "fontconfig"), "system",
            ),
        ])
        if sys.platform == "darwin":
            locations.append(CacheLocation(
                "homebrew_cache", "Homebrew 缓存", "Homebrew Cache",
                os.path.join(home, "Library", "Caches", "Homebrew"), "dev",
            ))
        else:
            locations.extend([
                CacheLocation(
                    "apt_cache", "apt 软件包缓存", "apt Package Cache",
                    "/var/cache/apt/archives", "dev", True,
                ),
                CacheLocation(
                    "dnf_cache", "DNF/Yum 软件包缓存", "DNF/Yum Package Cache",
                    "/var/cache/dnf", "dev", True,
                ),
                CacheLocation(
                    "pacman_cache", "Pacman 软件包缓存", "Pacman Package Cache",
                    "/var/cache/pacman/pkg", "dev", True,
                ),
                CacheLocation(
                    "yay_cache", "Yay/AUR 缓存", "Yay/AUR Cache",
                    os.path.join(home, ".cache", "yay"), "dev",
                ),
                CacheLocation(
                    "paru_cache", "Paru/AUR 缓存", "Paru/AUR Cache",
                    os.path.join(home, ".cache", "paru"), "dev",
                ),
            ])

    if sys.platform == "win32":
        locations.extend(_browser_cache_locations(
            local, "chrome", os.path.join("Google", "Chrome", "User Data"),
            "Chrome 缓存", "Chrome Cache",
        ))
        locations.extend(_browser_cache_locations(
            local, "edge", os.path.join("Microsoft", "Edge", "User Data"),
            "Edge 缓存", "Edge Cache",
        ))
        locations.extend(_firefox_cache_locations(roaming))
    else:
        browser_cache = os.path.join(home, ".cache")
        if sys.platform == "darwin":
            browser_cache = os.path.join(home, "Library", "Caches")
        locations.append(CacheLocation(
            "chrome_cache", "Chrome 缓存", "Chrome Cache",
            os.path.join(browser_cache, "google-chrome"), "browser",
        ))
        locations.append(CacheLocation(
            "firefox_cache", "Firefox 缓存", "Firefox Cache",
            os.path.join(browser_cache, "mozilla", "firefox"), "browser",
        ))
        if sys.platform == "darwin":
            locations.append(CacheLocation(
                "safari_cache", "Safari 缓存", "Safari Cache",
                os.path.join(home, "Library", "Caches", "com.apple.Safari"), "browser",
            ))

    locations.extend([
        CacheLocation(
            "npm_cache", "npm 缓存", "npm Cache",
            _pick(os.path.join(local, "npm-cache"), os.path.join(home, ".npm")), "dev",
        ),
        CacheLocation(
            "yarn_cache", "Yarn 缓存", "Yarn Cache",
            _pick(os.path.join(local, "Yarn", "Cache"), os.path.join(home, ".cache", "yarn")), "dev",
        ),
        CacheLocation(
            "pnpm_store", "pnpm 存储", "pnpm Store",
            _pick(os.path.join(local, "pnpm", "store"), os.path.join(home, ".local", "share", "pnpm", "store")), "dev",
        ),
        CacheLocation(
            "pip_cache", "pip 缓存", "pip Cache",
            _pick(os.path.join(local, "pip", "Cache"), os.path.join(home, ".cache", "pip")), "dev",
        ),
        CacheLocation(
            "uv_cache", "uv 缓存", "uv Cache",
            _pick(os.path.join(local, "uv", "cache"), os.path.join(home, ".cache", "uv")), "dev",
        ),
        CacheLocation(
            "poetry_cache", "Poetry 缓存", "Poetry Cache",
            _pick(os.path.join(local, "pypoetry", "Cache"), os.path.join(home, ".cache", "pypoetry")), "dev",
        ),
        CacheLocation(
            "maven_repo", "Maven 本地仓库", "Maven Repository",
            os.path.join(home, ".m2", "repository"), "dev",
        ),
        CacheLocation(
            "gradle_caches", "Gradle 缓存", "Gradle Caches",
            os.path.join(home, ".gradle", "caches"), "dev",
        ),
        CacheLocation(
            "nuget_packages", "NuGet 包缓存", "NuGet Package Cache",
            os.path.join(home, ".nuget", "packages"), "dev",
        ),
        CacheLocation(
            "go_build", "Go 构建缓存", "Go Build Cache",
            _pick(os.path.join(local, "go-build"), os.path.join(home, ".cache", "go-build")), "dev",
        ),
        CacheLocation(
            "cargo_registry", "Cargo 包缓存", "Cargo Registry Cache",
            os.path.join(home, ".cargo", "registry"), "dev",
        ),
        CacheLocation(
            "composer_cache", "Composer 缓存", "Composer Cache",
            _pick(os.path.join(roaming, "Composer"), os.path.join(home, ".cache", "composer")), "dev",
        ),
        CacheLocation(
            "conda_pkgs", "Conda 软件包缓存", "Conda Package Cache",
            _pick(
                os.path.join(local, "conda", "conda", "pkgs"),
                os.path.join(home, ".conda", "pkgs"),
            ),
            "dev", False, True,
        ),
        CacheLocation(
            "jetbrains_caches", "JetBrains IDE 缓存与日志", "JetBrains IDE Caches and Logs",
            _pick(
                os.path.join(local, "JetBrains"),
                os.path.join(home, ".cache", "JetBrains"),
            ),
            "dev", False, True,
        ),
        CacheLocation(
            "sccache", "sccache 编译缓存", "sccache Compiler Cache",
            _pick(
                os.path.join(local, "Mozilla", "sccache"),
                os.path.join(home, ".cache", "sccache"),
            ),
            "dev",
        ),
    ])

    vscode_data = _pick(
        os.path.join(roaming, "Code"),
        os.path.join(home, ".config", "Code"),
    )
    locations.extend(
        _vscode_cache_locations(vscode_data, "VS Code", "VS Code")
    )

    if sys.platform == "win32":
        locations.append(CacheLocation(
            "outlook_cache", "Outlook 离线缓存目录", "Outlook Offline Cache Folder",
            os.path.join(local, "Microsoft", "Outlook"), "app", False, True,
        ))
        locations.append(CacheLocation(
            "adobe_media_cache", "Adobe 媒体缓存", "Adobe Media Cache",
            os.path.join(local, "Adobe", "Common", "Media Cache Files"), "app",
        ))
        locations.extend([
            CacheLocation(
                "nvidia_dx_cache", "NVIDIA DX 着色器缓存", "NVIDIA DX Shader Cache",
                os.path.join(local, "NVIDIA", "DXCache"), "app",
            ),
            CacheLocation(
                "nvidia_gl_cache", "NVIDIA GL 着色器缓存", "NVIDIA GL Shader Cache",
                os.path.join(local, "NVIDIA", "GLCache"), "app",
            ),
            CacheLocation(
                "amd_dx_cache", "AMD DX 着色器缓存", "AMD DX Shader Cache",
                os.path.join(local, "AMD", "DxCache"), "app",
            ),
            CacheLocation(
                "amd_gl_cache", "AMD GL 着色器缓存", "AMD GL Shader Cache",
                os.path.join(local, "AMD", "GLCache"), "app",
            ),
            CacheLocation(
                "kodi_thumbs", "Kodi 缩略图", "Kodi Thumbnails",
                os.path.join(roaming, "Kodi", "userdata", "Thumbnails"), "app",
            ),
            CacheLocation(
                "steam_appcache", "Steam 应用缓存", "Steam App Cache",
                os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam", "appcache"), "app", False, True,
            ),
            CacheLocation(
                "docker_data", "Docker 数据目录", "Docker Data Directory",
                os.path.join(program_data, "Docker"), "app", False, True,
            ),
        ])
        locations.extend(_electron_cache_locations(local))
    else:
        locations.append(CacheLocation(
            "kodi_thumbs", "Kodi 缩略图", "Kodi Thumbnails",
            os.path.join(home, ".kodi", "userdata", "Thumbnails"), "app",
        ))
        locations.append(CacheLocation(
            "kodi_temp", "Kodi 临时目录", "Kodi Temp Directory",
            os.path.join(home, ".kodi", "temp"), "app",
        ))
        locations.append(CacheLocation(
            "steam_appcache", "Steam 应用缓存", "Steam App Cache",
            os.path.join(home, ".steam", "steam", "appcache"), "app", False, True,
        ))
        locations.append(CacheLocation(
            "docker_data", "Docker 数据目录", "Docker Data Directory",
            "/var/lib/docker", "app", True, True,
        ))

    return locations


def first_available_location():
    for location in get_cache_locations():
        if os.path.isdir(location.path):
            return location.path
    return tempfile.gettempdir()
def _browser_cache_locations(local, browser, folder, label_zh, label_en):
    user_data = os.path.join(local, folder)
    locations = []
    subdirs = (
        ("cache", "Cache", "网页缓存", "Web Cache"),
        ("code_cache", "Code Cache", "代码缓存", "Code Cache"),
        ("gpu_cache", "GPUCache", "GPU 缓存", "GPU Cache"),
        ("shader_cache", "ShaderCache", "着色器缓存", "Shader Cache"),
        ("service_worker", os.path.join("Service Worker", "CacheStorage"), "Service Worker 缓存", "Service Worker Cache"),
    )
    for profile in _profile_names(user_data):
        safe_profile = profile.lower().replace(" ", "_")
        for key_part, rel_path, zh_part, en_part in subdirs:
            locations.append(
                CacheLocation(
                    key=f"{browser}_{safe_profile}_{key_part}",
                    label_zh=f"{label_zh} - {profile} - {zh_part}",
                    label_en=f"{label_en} - {profile} - {en_part}",
                    path=os.path.join(user_data, profile, rel_path),
                    group="browser",
                )
            )
    return locations


def _firefox_cache_locations(roaming):
    profiles_root = os.path.join(roaming, "Mozilla", "Firefox", "Profiles")
    try:
        profiles = sorted(
            entry.name
            for entry in os.scandir(profiles_root)
            if entry.is_dir()
        )
    except OSError:
        profiles = []
    if not profiles:
        profiles = ["Default"]
    locations = []
    subdirs = (
        ("cache2", "网络缓存", "Network Cache"),
        ("startup", "启动缓存", "Startup Cache"),
        ("offline", "离线缓存", "Offline Cache"),
    )
    for profile in profiles:
        safe_profile = profile.lower().replace(" ", "_")
        for key_part, zh_part, en_part in subdirs:
            locations.append(
                CacheLocation(
                    key=f"firefox_{safe_profile}_{key_part}",
                    label_zh=f"Firefox - {profile} - {zh_part}",
                    label_en=f"Firefox - {profile} - {en_part}",
                    path=os.path.join(profiles_root, profile, key_part),
                    group="browser",
                )
            )
    return locations


def _vscode_cache_locations(data_root, label_zh, label_en):
    locations = []
    subdirs = (
        ("cache", "Cache", "网页缓存", "Web Cache"),
        ("code_cache", "Code Cache", "代码缓存", "Code Cache"),
        ("gpu_cache", "GPUCache", "GPU 缓存", "GPU Cache"),
        ("cached_data", "CachedData", "扩展缓存数据", "Cached Data"),
        ("cached_vsix", "CachedExtensionVSIXs", "扩展安装包缓存", "Cached Extension VSIXs"),
        ("service_worker", os.path.join("Service Worker", "CacheStorage"), "Service Worker 缓存", "Service Worker Cache"),
    )
    for key_part, rel_path, zh_part, en_part in subdirs:
        locations.append(
            CacheLocation(
                key=f"vscode_{key_part}",
                label_zh=f"{label_zh} - {zh_part}",
                label_en=f"{label_en} - {en_part}",
                path=os.path.join(data_root, rel_path),
                group="dev",
            )
        )
    return locations


def _electron_cache_locations(local):
    apps = (
        ("Discord", "Discord"),
        ("Slack", "Slack"),
        ("Notion", "Notion"),
        ("Postman", "Postman"),
        ("Obsidian", "Obsidian"),
        ("Teams", "Microsoft", "Teams"),
    )
    locations = []
    subdirs = (
        ("cache", "Cache", "网页缓存", "Web Cache"),
        ("code_cache", "Code Cache", "代码缓存", "Code Cache"),
        ("gpu_cache", "GPUCache", "GPU 缓存", "GPU Cache"),
        ("service_worker", os.path.join("Service Worker", "CacheStorage"), "Service Worker 缓存", "Service Worker Cache"),
    )
    for parts in apps:
        app_name = parts[0]
        for key_part, rel_path, zh_part, en_part in subdirs:
            locations.append(
                CacheLocation(
                    key=f"electron_{app_name.lower()}_{key_part}",
                    label_zh=f"{app_name} - {zh_part}",
                    label_en=f"{app_name} - {en_part}",
                    path=os.path.join(local, *parts[1:], rel_path),
                    group="app",
                )
            )
    return locations
