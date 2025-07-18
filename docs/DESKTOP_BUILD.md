# 桌面應用程式構建指南

本文檔說明如何構建 MCP Feedback Enhanced 的桌面應用程式。

## 先決條件

### 必需工具

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Rust 工具鏈**
   ```bash
   # 安裝 Rust (如果尚未安裝)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

   # 驗證安裝
   rustc --version
   cargo --version
   ```

3. **Tauri CLI** (自動安裝)
   ```bash
   cargo install tauri-cli
   ```

### 开发依赖

```bash
# 安装 Python 开发依赖
uv sync --dev

# 或使用 pip
pip install -e ".[dev]"
```

## 构建方法

### 方法 1: 使用 Makefile (推荐)

```bash
# 构建 Debug 版本
make build-desktop

# 构建 Release 版本
make build-desktop-release

# 构建并测试
make test-desktop

# 清理构建产物
make clean-desktop

# 完整构建流程 (包含 PyPI 包)
make build-all
```

### 方法 2: 直接使用 Python 脚本

```bash
# 构建 Debug 版本
python scripts/build_desktop.py

# 构建 Release 版本
python scripts/build_desktop.py --release

# 清理构建产物
python scripts/build_desktop.py --clean

# 查看帮助
python scripts/build_desktop.py --help
```

## 构建产物

构建完成后，产物将位于：

```
src/mcp_feedback_enhanced/
├── desktop_release/                                   # 發佈用二進制文件
│   ├── __init__.py
│   ├── mcp-feedback-enhanced-desktop.exe              # Windows
│   ├── mcp-feedback-enhanced-desktop-macos-intel     # macOS Intel
│   ├── mcp-feedback-enhanced-desktop-macos-arm64     # macOS Apple Silicon
│   └── mcp-feedback-enhanced-desktop-linux           # Linux
├── desktop_app/                                       # 發佈用 Python 模組
│   ├── __init__.py
│   └── desktop_app.py
└── ...

src-tauri/python/mcp_feedback_enhanced_desktop/        # 開發環境模組
├── __init__.py
├── desktop_app.py
└── ...
```

### 多平台支援

構建腳本會自動構建以下平台的二進制文件：

- **Windows**: `mcp-feedback-enhanced-desktop.exe`
- **macOS Intel**: `mcp-feedback-enhanced-desktop-macos-intel`
- **macOS Apple Silicon**: `mcp-feedback-enhanced-desktop-macos-arm64`
- **Linux**: `mcp-feedback-enhanced-desktop-linux`

桌面应用会根据运行平台自动选择对应的二进制文件。

## 测试桌面应用程序

```bash
# 方法 1: 直接测试
python -m mcp_feedback_enhanced test --desktop

# 方法 2: 使用 Makefile
make test-desktop
```

## 跨平台注意事项

### Windows
- 桌面应用程序不会显示额外的 CMD 窗口
- 二进制文件: `mcp-feedback-enhanced-desktop.exe`

### Linux/macOS
- 二进制文件: `mcp-feedback-enhanced-desktop`
- 自动设置执行权限

## 故障排除

### 常见问题

1. **Rust 未安装**
   ```
   ❌ Rust 未安装，请访问 https://rustup.rs/
   ```
   解决方案: 安装 Rust 工具链

2. **Tauri CLI 未安装**
   ```
   ⚠️ Tauri CLI 未安装，正在安装...
   ```
   解决方案: 脚本会自动安装，或手动执行 `cargo install tauri-cli`

3. **構建失敗**
   ```
   ❌ 構建失敗
   ```
   解決方案: 檢查 Rust 環境，清理後重新構建
   ```bash
   make clean-desktop
   make build-desktop
   ```

### 檢查環境

```bash
# 檢查 Rust 環境
make check-rust

# 檢查所有依賴
make dev-setup
```

### 跨平台編譯要求

構建腳本會自動安裝以下 Rust targets：

```bash
# 這些 targets 會自動安裝，無需手動執行
rustup target add x86_64-pc-windows-msvc      # Windows
rustup target add x86_64-apple-darwin         # macOS Intel
rustup target add aarch64-apple-darwin        # macOS Apple Silicon
rustup target add x86_64-unknown-linux-gnu    # Linux
```

**注意**:
- 本地構建通常只能成功構建當前平台的二進制文件
- 跨平台編譯需要複雜的工具鏈配置（C 編譯器、系統庫等）
- **完整的多平台支援在 GitHub Actions CI 中實現**
- 發佈到 PyPI 時會自動包含所有平台的二進制文件

## 自動化構建

### CI/CD 多平台構建

GitHub Actions 會在各自的原生平台上構建桌面應用：

```yaml
# 多平台構建策略
strategy:
  matrix:
    include:
      - os: windows-latest    # Windows 原生構建
        target: x86_64-pc-windows-msvc
      - os: macos-latest      # macOS 原生構建
        target: x86_64-apple-darwin
      - os: ubuntu-latest     # Linux 原生構建
        target: x86_64-unknown-linux-gnu
```

這確保了：
- ✅ 每個平台在其原生環境中構建
- ✅ 避免跨平台編譯的複雜性
- ✅ 最終 PyPI 包包含所有平台的二進制文件

### 本地自動化

```bash
# 完整的開發工作流程
make dev-setup      # 初始化環境
make quick-check    # 程式碼檢查
make build-all      # 構建所有組件
make test-all       # 測試所有功能
```

## 發布流程

1. **構建發布版本**
   ```bash
   make build-desktop-release
   ```

2. **構建 PyPI 包**
   ```bash
   make build-all
   ```

3. **驗證包內容**
   ```bash
   # 檢查桌面應用程式是否包含在包中
   tar -tf dist/*.tar.gz | grep desktop
   ```

桌面應用程式現在已完全集成到 PyPI 包中，包含所有主要平台的二進制文件，用戶安裝後可直接使用 `--desktop` 選項啟動。

### 平台兼容性

- **Windows**: 支援 x64 架構
- **macOS**: 支援 Intel 和 Apple Silicon (M1/M2) 架構
- **Linux**: 支援 x64 架構

桌面應用會自動檢測運行平台並選擇對應的二進制文件。
