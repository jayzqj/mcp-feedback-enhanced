# CLAUDE.md

此文件为Claude Code (claude.ai/code)在此代码库中工作时提供指导。

## 交流语言

**重要：此项目要求使用简体中文进行交流。** 与用户的所有交互都应使用简体中文，包括代码注释、文档编写和对话回复。

## 项目概述

MCP Feedback Enhanced是一个增强的MCP（模型上下文协议）服务器，提供交互式用户反馈收集功能，支持双界面（Web UI和桌面应用）。它专为AI辅助开发工作流程设计，支持SSH远程、WSL和本地环境。

**核心功能：**
- 双界面架构（Web UI + 桌面应用）
- 智能环境检测（SSH远程、WSL、本地）
- 通过WebSocket进行交互式反馈收集
- 多语言支持（繁体中文/简体中文、英文）
- 图片上传和处理
- 会话管理和历史记录跟踪

## 开发命令

### 环境设置
```bash
# 安装依赖
uv sync

# 开发环境设置（包含pre-commit钩子）
make dev-setup

# 仅安装开发依赖
make install-dev
```

### 测试命令
```bash
# 运行单元测试
make test

# 运行带覆盖率的测试
make test-cov

# 运行功能测试（标准MCP工具测试）
make test-func

# 运行Web UI测试（持续运行用于开发）
make test-web

# 运行桌面应用功能测试
make test-desktop-func

# 运行所有测试
make test-all
```

### 代码质量
```bash
# 快速检查并自动修复（推荐用于开发）
make quick-check

# 运行所有代码质量检查
make check

# 运行检查并自动修复
make check-fix

# 单独的质量检查
make lint              # Ruff代码检查
make lint-fix         # Ruff代码检查并自动修复
make format           # 代码格式化
make type-check       # MyPy类型检查
```

### 桌面应用（v2.5.0+）
```bash
# 构建桌面应用（调试模式）
make build-desktop

# 构建桌面应用（发布模式）
make build-desktop-release

# 测试桌面应用
make test-desktop

# 清理桌面构建产物
make clean-desktop

# 检查Rust环境
make check-rust
```

### 包管理
```bash
# 构建包
make build

# 清理缓存和临时文件
make clean

# 更新依赖
make update-deps
```

## 代码架构

### 核心结构
```
src/mcp_feedback_enhanced/
├── server.py              # 主要MCP服务器实现
├── __main__.py            # CLI入口点
├── web/                   # Web UI实现
│   ├── main.py           # FastAPI网络服务器
│   ├── routes/           # API路由
│   ├── static/           # 前端资源（JS、CSS、HTML）
│   ├── templates/        # Jinja2模板
│   └── utils/            # Web工具
├── desktop_app/          # 桌面应用（基于Tauri）
├── utils/                # 共享工具
│   ├── error_handler.py  # 错误处理框架
│   ├── memory_monitor.py # 内存监控
│   └── resource_manager.py # 资源管理
└── i18n.py              # 国际化
```

### 关键组件

**MCP服务器层** (`server.py`):
- 实现`interactive_feedback` MCP工具
- 处理环境检测（SSH远程、WSL、本地）
- 管理界面选择（Web UI vs 桌面应用）
- 处理图片和用户反馈

**Web UI层** (`web/main.py`):
- 基于FastAPI的网络服务器，支持WebSocket
- 单活跃会话管理
- 与AI助手实时通信
- 会话持久化和历史记录跟踪

**桌面应用** (`desktop_app/`):
- 基于Tauri的跨平台桌面应用
- 使用相同的Web UI后端
- 为Windows/macOS/Linux提供原生桌面体验

**前端架构** (`web/static/js/`):
- 模块化JavaScript架构
- WebSocket管理器用于实时通信
- 会话管理和UI状态处理
- 图片上传和处理
- 音频通知系统

### 重要设计模式

**单活跃会话**：系统一次只维护一个活跃的反馈会话，替代传统的多会话管理，以获得更好的性能和用户体验。

**环境检测**：自动检测SSH远程、WSL和本地环境，并选择适当的界面。

**错误处理**：集中式错误处理框架（`utils/error_handler.py`），具有分类的错误类型和恢复策略。

**资源管理**：自动清理临时文件，为长期运行的会话进行内存监控。

## 配置

### 环境变量
- `MCP_DEBUG`：启用调试日志（`true`/`false`）
- `MCP_WEB_HOST`：Web UI主机绑定（默认：`127.0.0.1`）
- `MCP_WEB_PORT`：Web UI端口（默认：`8765`）
- `MCP_DESKTOP_MODE`：启用桌面应用模式（`true`/`false`）
- `MCP_LANGUAGE`：强制UI语言（`zh-TW`/`zh-CN`/`en`）

### MCP配置示例
```json
// Web UI模式
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}

// 桌面模式
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx", 
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DESKTOP_MODE": "true"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

## 测试策略

**单元测试**：位于`tests/unit/` - 测试单个模块和工具
**集成测试**：位于`tests/integration/` - 测试组件交互
**功能测试**：端到端测试完整的MCP工具工作流程

运行特定测试类别：
```bash
pytest tests/unit/              # 仅单元测试
pytest tests/integration/       # 仅集成测试
pytest -m "not slow"           # 仅快速测试
```

## 开发指导原则

### 代码质量标准
- **代码检查**：Ruff，具有全面的规则集
- **类型检查**：MyPy，采用渐进式类型方法
- **格式化**：Ruff格式化器，风格一致
- **Pre-commit**：提交时自动质量检查

### 国际化
- 所有面向用户的文本必须支持i18n
- 语言文件：`src/mcp_feedback_enhanced/web/locales/`
- 支持的语言：繁体中文、简体中文、英文

### 安全考虑
- 对所有用户上传进行输入验证
- 安全处理临时文件
- WebSocket连接安全
- 不记录敏感信息

## 特别说明

**双界面支持**：此项目支持Web UI和桌面应用模式。在进行更改时，请确保与两个界面的兼容性。

**环境兼容性**：代码必须在SSH远程、WSL和本地环境中工作。请仔细测试环境检测逻辑。

**会话管理**：系统使用单活跃会话模型。在修改会话相关代码之前，请理解会话生命周期。

**内存管理**：长期运行的会话需要仔细的内存管理。使用内置的内存监控器和资源管理器工具。