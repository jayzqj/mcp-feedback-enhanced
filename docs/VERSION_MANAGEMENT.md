# 版本管理系统

## 概述

本项目使用统一的版本管理系统，确保所有文件中的版本号保持一致。

## 版本格式

```
YYYY.MMDD.PATCH
```

- **YYYY**: 年份 (如: 2025)
- **MMDD**: 月日 (4位数，如: 0808 表示8月8日)
- **PATCH**: 补丁版本号 (如: 1, 2, 3...)

示例: `2025.808.1`

## 统一版本源

所有版本信息都存储在 `src/mcp_feedback_enhanced/_version.py` 文件中：

```python
__version__ = "2025.808.1"
__author__ = "jayzqj"
__email__ = ""
```

## 版本同步的文件

以下文件会自动与统一版本源保持同步：

1. **Python 包文件**:
   - `src/mcp_feedback_enhanced/__init__.py`
   - `src/mcp_feedback_enhanced/desktop_app/__init__.py`
   - `src-tauri/python/mcp_feedback_enhanced_desktop/__init__.py`

2. **配置文件**:
   - `pyproject.toml`
   - `src-tauri/tauri.conf.json`
   - `src-tauri/Cargo.toml`
   - `.bumpversion.cfg`

## 使用方法

### 检查版本一致性

```bash
# 使用 Make 命令
make check-version

# 或直接运行脚本
python scripts/sync_version.py --check-only
```

### 同步版本号

```bash
# 使用 Make 命令
make sync-version

# 或直接运行脚本
python scripts/sync_version.py
```

### 更新版本号

```bash
# 更新补丁版本 (2025.808.1 -> 2025.808.2)
make bump-patch

# 更新次版本 (2025.808.1 -> 2025.809.0)
make bump-minor

# 更新主版本 (2025.808.1 -> 2026.0.0)
make bump-major
```

**注意**: 使用 `bump-*` 命令会自动运行版本同步。

### 手动更新版本

如果需要手动设置特定版本号：

1. 编辑 `src/mcp_feedback_enhanced/_version.py`
2. 运行 `make sync-version` 同步到所有文件

## 版本导入

在代码中导入版本信息：

```python
# 主包
from mcp_feedback_enhanced import __version__, __author__

# 从版本文件直接导入
from mcp_feedback_enhanced._version import __version__, get_version_info

# 获取详细版本信息
version_info = get_version_info()
```

## 版本兼容性检查

```python
from mcp_feedback_enhanced._version import check_version_compatibility

# 检查是否兼容指定版本
is_compatible = check_version_compatibility("2025.800.0")
```

## 开发工作流程

1. **开发新功能**: 无需关心版本号
2. **准备发布**: 运行 `make bump-patch/minor/major`
3. **验证版本**: 运行 `make check-version`
4. **构建发布**: 运行 `make build`

## 故障排除

### 版本不一致

如果发现版本号不一致：

```bash
# 检查哪些文件版本不一致
make check-version

# 同步所有文件版本
make sync-version
```

### 导入错误

如果遇到版本导入错误：

1. 确保 `src/mcp_feedback_enhanced/_version.py` 存在
2. 检查文件语法是否正确
3. 运行 `python -c "from src.mcp_feedback_enhanced._version import __version__; print(__version__)"`

## 最佳实践

1. **始终使用统一版本源**: 不要在其他文件中硬编码版本号
2. **使用 Make 命令**: 优先使用 `make bump-*` 而不是直接使用 `bump2version`
3. **发布前检查**: 发布前运行 `make check-version` 确保版本一致性
4. **自动化集成**: 在 CI/CD 中集成版本检查

## 相关文件

- `src/mcp_feedback_enhanced/_version.py` - 统一版本源
- `scripts/sync_version.py` - 版本同步脚本
- `.bumpversion.cfg` - bump2version 配置
- `Makefile` - 版本管理命令
