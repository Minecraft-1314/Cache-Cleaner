  # Cache Cleaner

查找并一键清理电脑中的缓存文件与缓存目录

A cross-platform desktop tool to find and clean up cache files and directories on your computer with ease.

---

## 核心特性 | Core Features

- **完整目录清单**：内置系统、浏览器、开发工具、应用缓存目录，可按分组勾选，一个或多个目录同时扫描<br>
  **Complete Directory Catalog**: Built-in cache directories for system, browser, developer tools and applications; check one or more directories and scan them together

- **完整后缀清单**：支持常见缓存/临时/构建后缀，可按分组勾选，并手动指定目录递归查找<br>
  **Complete Suffix Catalog**: Supports common cache, temporary and build suffixes; check suffixes and manually choose a directory for recursive search

- **多目录扫描**：目录模式并行处理多个勾选缓存目录，快速汇总扫描结果<br>
  **Multi Directory Scan**: Scans multiple checked cache directories in parallel and aggregates the results

- **真实空间统计**：目录按实际内容累计大小，支持按占用空间排序，并实时估算可释放空间<br>
  **Real Space Estimation**: Calculates real directory size, sorts by occupied space and estimates reclaimable space in real time

- **安全删除**：默认移动至回收站，删除前二次确认；清理失败的项目保留并标记，便于重试<br>
  **Safe Deletion**: Moves items to the Recycle Bin by default, asks for confirmation before deletion, and keeps failed items visible for retry

- **智能排除**：支持通配符规则排除特定项目，扫描结果可通过右键快速排除<br>
  **Smart Exclude**: Supports wildcard exclude rules and quick exclusion from the context menu

- **多语言支持**：内置中文和英文，可随时切换<br>
  **Multi language Support**: Built in Chinese and English, switchable anytime

- **便捷操作**：扫描进度实时显示，支持停止扫描/停止清理；全选/取消全选，单击勾选；排序与本地过滤<br>
  **Convenient Operation**: Real time scan progress, stop scan/clean, select all/deselect all, click to select, sort and local filtering

---

## 使用说明 | Usage Guide

1. 安装依赖（Python 3.10+）：`pip install -r requirements.txt`<br>
   Install the dependencies (Python 3.10+): `pip install -r requirements.txt`

2. 从源码运行程序：在项目目录执行 `python cache_cleaner.py`<br>
   Run the program from source with `python cache_cleaner.py`

3. 选择扫描方式；缓存目录模式下勾选需要扫描的缓存目录<br>
   Choose a scan mode; in Cache Directory mode, check the cache directories you want to scan

4. 缓存后缀递归查找模式下，勾选需要匹配的后缀，并手动点击“选择目录”指定扫描目录<br>
   In Recursive Cache Suffix Scan mode, check the suffixes and manually pick a directory with “Choose Directory”

5. 点击“开始扫描”后，扫描结果实时出现在表格中；程序启动和修改勾选时不会自动扫描<br>
   Click “Start Scan”, and results appear in the table in real time; the program does not auto scan on startup or after selection changes

6. 在结果列表中勾选需要清理的缓存项，可搜索、排序并查看预计释放空间<br>
   Check the cache items you want to clean; search, sort and review the estimated reclaimable space

7. 点击“开始清理”，确认后即可删除；默认移动至回收站，被占用或权限不足的项目会保留在列表中供重试<br>
   Click “Clean Selected”, confirm, and the items will be cleaned; items go to the Recycle Bin by default, and locked or permission-denied items remain available for retry

8. 可通过“排除规则”设置通配符规则，匹配的项目将不在扫描结果中出现<br>
   You can set wildcard rules via “Exclude Rules”; matched items will be excluded from scan results

---

## 项目贡献者 | Contributors

| 贡献者 (Contributor) | 贡献内容 (Contribution) |
|----------------------|--------------------------|
| Minecraft-1314 | 完整开发 (Complete development) |
| *(欢迎提交 PR 加入贡献者列表)* | *(Welcome to submit PR to join the contributor list)* |

---

## 许可协议 | License

本项目采用 MIT 许可证，详情参见 `LICENSE` 文件。  
This project is licensed under the MIT License, see the `LICENSE` file for details.

---

## 支持我们 | Support Us

如果这个项目对您有帮助，欢迎点亮右上角的 Star ⭐ 支持我们，这将是对所有贡献者最大的鼓励！  
If this project is helpful to you, please feel free to star it in the upper right corner ⭐ to support us, which will be the greatest encouragement to all contributors!
