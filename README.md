# MCP Feedback Enhanced（交互反馈增强版）

**原作者：** [Fábio Ferreira](https://x.com/fabiomlferreira) | [原始项目](https://github.com/noopstudios/interactive-feedback-mcp) ⭐
**增强分支：** [Minidoracat](https://github.com/Minidoracat)
**UI 设计参考：** [sanshao85/mcp-feedback-collector](https://github.com/sanshao85/mcp-feedback-collector)

## 🎯 核心概念

这是一个 [MCP 服务器](https://modelcontextprotocol.io/)，建立**反馈导向的开发工作流程**，提供**Web UI 和桌面应用程序**双重选择，完美适配本地、**SSH 远程开发环境**与 **WSL (Windows Subsystem for Linux) 环境**。通过引导 AI 与用户确认而非进行推测性操作，可将多次工具调用合并为单次反馈导向请求，大幅节省平台成本并提升开发效率。

**🌐 双重界面架构优势：**
- 🖥️ **桌面应用程序**：原生跨平台桌面体验，支持 Windows、macOS、Linux
- 🌐 **Web UI 界面**：无需 GUI 依赖，适合远程和 WSL 环境
- 🔧 **灵活部署**：根据环境需求选择最适合的界面模式
- 📦 **统一功能**：两种界面提供完全相同的功能体验

**🖥️ 桌面应用程序：** v2.5.0 新增跨平台桌面应用程序支持，基于 Tauri 框架，支持 Windows、macOS、Linux 三大平台，提供原生桌面体验。

**支持平台：** [Cursor](https://www.cursor.com) | [Cline](https://cline.bot) | [Windsurf](https://windsurf.com) | [Augment](https://www.augmentcode.com) | [Trae](https://www.trae.ai)

### 🔄 工作流程
1. **AI 调用** → `mcp-feedback-enhanced` 工具
2. **界面启动** → 自动开启桌面应用程序或浏览器界面（根据配置）
3. **智能互动** → 提示词选择、文字输入、图片上传、自动提交
4. **即时反馈** → WebSocket 连线即时传递信息给 AI
5. **会话追踪** → 自动记录会话历史与统计
6. **流程继续** → AI 根据反馈调整行为或结束任务

## 🌟 主要功能

### 🖥️ 双重界面支持
- **桌面应用程序**：基于 Tauri 的跨平台原生应用程序，支持 Windows、macOS、Linux
- **Web UI 界面**：轻量级浏览器界面，适合远程和 WSL 环境
- **自动环境检测**：智能识别 SSH Remote、WSL 和其他特殊环境
- **统一功能体验**：两种界面提供完全相同的功能

### 📝 智能工作流
- **提示词管理**：常用提示词的 CRUD 操作、使用统计、智能排序
- **自动定时提交**：1-86400 秒灵活计时器，支持暂停、恢复、取消，新增暂停/恢复按钮控制
- **自动命令执行** (v2.6.0)：在创建新会话或提交后自动执行预设命令，提升开发效率
- **会话管理与追踪**：本地文件存储、隐私控制、历史导出（支持 JSON、CSV、Markdown 格式）、实时统计、灵活超时设置
- **连接监控**：WebSocket 状态监控、自动重连、质量指标
- **AI 工作摘要 Markdown 显示**：支持丰富的 Markdown 语法渲染，包括标题、粗体文本、代码块、列表、链接等格式，增强内容可读性

### 🎨 现代化体验
- **响应式设计**：适应不同屏幕尺寸，模块化 JavaScript 架构
- **音效通知**：内置多种音效，支持自定义音频上传，音量控制
- **系统通知** (v2.6.0)：重要事件的系统级实时警报（如自动提交、会话超时）
- **智能记忆**：输入框高度记忆、一键复制、持久化设置
- **简体中文支持**：完整的简体中文界面，即时切换

### 🖼️ 图片与媒体
- **全格式支持**：PNG、JPG、JPEG、GIF、BMP、WebP
- **便捷上传**：拖拽文件、剪贴板粘贴 (Ctrl+V)
- **无限制处理**：支持任意大小图片，自动智能处理

## 🌐 界面预览

### Web UI 界面 (v2.5.0 - 桌面应用程序支持)

<div align="center">
  <img src="docs/zh-CN/images/web1.png" width="400" alt="Web UI 主界面 - 提示词管理与自动提交" />
</div>

<details>
<summary>📱 点击查看完整界面截图</summary>

<div align="center">
  <img src="docs/zh-CN/images/web2.jpeg" width="800" alt="Web UI 完整界面 - 会话管理与设置" />
</div>

</details>

*Web UI 界面 - 支持桌面应用程序和 Web 界面，提供提示词管理、自动提交、会话追踪等智能功能*

### 桌面应用程序界面 (v2.5.0 新功能)

<div align="center">
  <img src="docs/zh-CN/images/desktop1.png" width="600" alt="桌面应用程序 - 原生跨平台桌面体验" />
</div>

*桌面应用程序 - 基于 Tauri 框架的原生跨平台桌面应用程序，支持 Windows、macOS、Linux，功能与 Web UI 完全相同*

**快捷键支持**
- `Ctrl+Enter`（Windows/Linux）/ `Cmd+Enter`（macOS）：提交反馈（支持主键盘和数字键盘）
- `Ctrl+V`（Windows/Linux）/ `Cmd+V`（macOS）：直接粘贴剪贴板图片
- `Ctrl+I`（Windows/Linux）/ `Cmd+I`（macOS）：快速聚焦输入框 (感谢 @penn201500)

## 🚀 快速开始

### 1. 安装与测试
```bash
# 安装 uv（如果尚未安装）
pip install uv
```

### 2. 配置 MCP
**基础配置**（适合大多数用户）：
```json
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
```

**高级配置**（需要自定义环境）：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DEBUG": "false",
        "MCP_WEB_HOST": "127.0.0.1",
        "MCP_WEB_PORT": "8765",
        "MCP_LANGUAGE": "zh-CN"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

**桌面应用程序配置**（v2.5.0 新功能 - 使用原生桌面应用程序）：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DESKTOP_MODE": "true",
        "MCP_WEB_HOST": "127.0.0.1",
        "MCP_WEB_PORT": "8765",
        "MCP_DEBUG": "false"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

**配置文件示例**：
- 桌面模式：[examples/mcp-config-desktop.json](examples/mcp-config-desktop.json)
- Web 模式：[examples/mcp-config-web.json](examples/mcp-config-web.json)

### 3. 提示工程设置
为了获得最佳效果，请在您的 AI 助手中添加以下规则：

```
# MCP 交互反馈规则

遵循 mcp-feedback-enhanced 指令
```

## ⚙️ 高级设置

### 环境变量
| 变量 | 用途 | 值 | 默认值 |
|----------|---------|--------|---------|
| `MCP_DEBUG` | 调试模式 | `true`/`false` | `false` |
| `MCP_WEB_HOST` | Web UI 主机绑定 | IP 地址或主机名 | `127.0.0.1` |
| `MCP_WEB_PORT` | Web UI 端口 | `1024-65535` | `8765` |
| `MCP_DESKTOP_MODE` | 桌面应用程序模式 | `true`/`false` | `false` |
| `MCP_LANGUAGE` | 强制 UI 语言 | `zh-CN` | 自动检测 |

**`MCP_WEB_HOST` 说明**：
- `127.0.0.1`（默认）：仅本地访问，安全性更高
- `0.0.0.0`：允许远程访问，适合 SSH 远程开发环境

**`MCP_LANGUAGE` 说明**：
- 用于强制界面语言，覆盖自动系统检测
- 支持的语言代码：
  - `zh-CN`：简体中文
- 语言检测优先级：
  1. 界面中用户保存的语言设置（最高优先级）
  2. `MCP_LANGUAGE` 环境变量
  3. 系统环境变量（LANG、LC_ALL 等）
  4. 系统默认语言
  5. 回退到默认语言（简体中文）

### 测试选项
```bash
# 版本检查
uvx mcp-feedback-enhanced@latest version       # 检查版本

# 界面测试
uvx mcp-feedback-enhanced@latest test --web    # 测试 Web UI（自动持续运行）
uvx mcp-feedback-enhanced@latest test --desktop # 测试桌面应用程序（v2.5.0 新功能）

# 调试模式
MCP_DEBUG=true uvx mcp-feedback-enhanced@latest test

# 指定语言进行测试
MCP_LANGUAGE=zh-CN uvx mcp-feedback-enhanced@latest test --web  # 强制简体中文界面
```

### 开发者安装
```bash
git clone https://github.com/Minidoracat/mcp-feedback-enhanced.git
cd mcp-feedback-enhanced
uv sync
```

**本地测试方法**
```bash
# 功能测试
make test-func                                           # 标准功能测试
make test-web                                            # Web UI 测试（持续运行）
make test-desktop-func                                   # 桌面应用程序功能测试

# 或使用直接命令
uv run python -m mcp_feedback_enhanced test              # 标准功能测试
uvx --no-cache --with-editable . mcp-feedback-enhanced test --web   # Web UI 测试（持续运行）
uvx --no-cache --with-editable . mcp-feedback-enhanced test --desktop # 桌面应用程序测试

# 桌面应用程序构建（v2.5.0 新功能）
make build-desktop                                       # 构建桌面应用程序（调试模式）
make build-desktop-release                               # 构建桌面应用程序（发布模式）
make test-desktop                                        # 测试桌面应用程序
make clean-desktop                                       # 清理桌面构建产物

# 单元测试
make test                                                # 运行所有单元测试
make test-fast                                          # 快速测试（跳过慢速测试）
make test-cov                                           # 测试并生成覆盖率报告

# 代码质量检查
make check                                              # 完整代码质量检查
make quick-check                                        # 快速检查和自动修复
```

**测试说明**
- **功能测试**：测试完整的 MCP 工具功能工作流程
- **单元测试**：测试各个模块功能
- **覆盖率测试**：生成 HTML 覆盖率报告到 `htmlcov/` 目录
- **质量检查**：包括代码检查、格式化、类型检查

## 🆕 版本历史

📋 **完整版本历史：** [RELEASE_NOTES/CHANGELOG.md](RELEASE_NOTES/CHANGELOG.md)

### 最新版本亮点 (v2.6.0)
- 🚀 **自动命令执行**：在创建新会话或提交后自动执行预设命令，提升工作流程效率
- 📊 **会话导出功能**：支持将会话记录导出为多种格式，便于分享和存档
- ⏸️ **自动提交控制**：新增暂停和恢复按钮，更好地控制自动提交时机
- 🔔 **系统通知**：重要事件的系统级通知，实时警报
- ⏱️ **会话超时优化**：重新设计会话管理，提供更灵活的配置选项
- 🌏 **国际化增强**：重构国际化架构，完整的简体中文支持
- 🎨 **UI 简化**：大幅简化用户界面，提升用户体验

## 🐛 常见问题

### 🌐 SSH 远程环境问题
**问：SSH Remote 环境下浏览器无法启动或访问**
答：有两种解决方案：

**方案 1：环境变量设置（v2.5.5 推荐）**
在 MCP 配置中设置 `"MCP_WEB_HOST": "0.0.0.0"` 以允许远程访问：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_WEB_HOST": "0.0.0.0",
        "MCP_WEB_PORT": "8765"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```
然后在本地浏览器中打开：`http://[远程主机IP]:8765`

**方案 2：SSH 端口转发（传统方法）**
1. 使用默认配置（`MCP_WEB_HOST`: `127.0.0.1`）
2. 设置 SSH 端口转发：
   - **VS Code Remote SSH**：按 `Ctrl+Shift+P` → "Forward a Port" → 输入 `8765`
   - **Cursor SSH Remote**：手动添加端口转发规则（端口 8765）
3. 在本地浏览器中打开：`http://localhost:8765`

详细解决方案请参考：[SSH 远程环境使用指南](docs/zh-CN/ssh-remote/browser-launch-issues.md)

**问：为什么收不到新的 MCP 反馈？**
答：可能是 WebSocket 连接问题。**解决方案**：直接刷新浏览器页面。

**问：为什么 MCP 没有被调用？**
答：请确认 MCP 工具状态显示绿灯。**解决方案**：反复切换 MCP 工具开关，等待几秒钟让系统重新连接。

**问：Augment 无法启动 MCP**
答：**解决方案**：完全关闭并重启 VS Code 或 Cursor，重新打开项目。

### 🔧 一般问题
**问：如何使用桌面应用程序？**
答：v2.5.0 引入跨平台桌面应用程序支持。在 MCP 配置中设置 `"MCP_DESKTOP_MODE": "true"` 以启用：
```json
{
  "mcpServers": {
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "env": {
        "MCP_DESKTOP_MODE": "true",
        "MCP_WEB_PORT": "8765"
      },
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```
**配置文件示例**：[examples/mcp-config-desktop.json](examples/mcp-config-desktop.json)

**问：如何使用旧版 PyQt6 GUI 界面？**
答：v2.4.0 完全移除了 PyQt6 GUI 依赖。要使用旧版 GUI，请指定 v2.3.0 或更早版本：`uvx mcp-feedback-enhanced@2.3.0`
**注意**：旧版本不包含新功能（提示词管理、自动提交、会话管理、桌面应用程序等）。

**问：出现 "Unexpected token 'D'" 错误**
答：调试输出干扰。设置 `MCP_DEBUG=false` 或移除环境变量。

**问：中文字符乱码**
答：已在 v2.0.3 修复。更新到最新版本：`uvx mcp-feedback-enhanced@latest`

**问：多屏环境下窗口消失或定位错误**
答：已在 v2.1.1 修复。前往 "⚙️ 设置" 标签页，勾选 "始终在主屏幕中央显示窗口" 来解决。特别适合 T 型屏幕排列和其他复杂多屏配置。

**问：图片上传失败**
答：检查文件格式（PNG/JPG/JPEG/GIF/BMP/WebP）。系统支持任意大小的图片文件。

**问：Web UI 无法启动**
答：检查防火墙设置或尝试使用不同端口。

**问：UV 缓存占用磁盘空间过大**
答：由于频繁使用 `uvx` 命令，缓存可能累积到数十 GB。建议定期清理：
```bash
# 查看缓存大小和详细信息
python scripts/cleanup_cache.py --size

# 预览清理内容（不实际清理）
python scripts/cleanup_cache.py --dry-run

# 执行标准清理
python scripts/cleanup_cache.py --clean

# 强制清理（尝试关闭相关程序，解决 Windows 文件占用问题）
python scripts/cleanup_cache.py --force

# 或直接使用 uv 命令
uv cache clean
```
详细说明请参考：[缓存管理指南](docs/zh-CN/cache-management.md)

**问：AI 模型无法解析图片**
答：各种 AI 模型（包括 Gemini Pro 2.5、Claude 等）在图片解析方面可能存在不稳定性，有时能正确识别，有时无法解析上传的图片内容。这是 AI 视觉理解技术的已知限制。建议：
1. 确保图片质量良好（高对比度、清晰文字）
2. 尝试多次上传，重试通常会成功
3. 如果解析持续失败，尝试调整图片大小或格式

## 🙏 致谢

### 🌟 支持原作者
**Fábio Ferreira** - [X @fabiomlferreira](https://x.com/fabiomlferreira)
**原始项目：** [noopstudios/interactive-feedback-mcp](https://github.com/noopstudios/interactive-feedback-mcp)

如果您觉得有用，请：
- ⭐ [为原始项目点星](https://github.com/noopstudios/interactive-feedback-mcp)
- 📱 [关注原作者](https://x.com/fabiomlferreira)

### 设计灵感
**sanshao85** - [mcp-feedback-collector](https://github.com/sanshao85/mcp-feedback-collector)

### 贡献者
**penn201500** - [GitHub @penn201500](https://github.com/penn201500)
- 🎯 自动聚焦输入框功能 ([PR #39](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/39))

**leo108** - [GitHub @leo108](https://github.com/leo108)
- 🌐 SSH 远程开发支持（`MCP_WEB_HOST` 环境变量）([PR #113](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/113))

**Alsan** - [GitHub @Alsan](https://github.com/Alsan)
- 🍎 macOS PyO3 编译配置支持 ([PR #93](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/93))

**fireinice** - [GitHub @fireinice](https://github.com/fireinice)
- 📝 工具文档优化（LLM 指令移至 docstring）([PR #105](https://github.com/Minidoracat/mcp-feedback-enhanced/pull/105))

### 社区支持
- **Discord：** [https://discord.gg/Gur2V67](https://discord.gg/Gur2V67)
- **问题反馈：** [GitHub Issues](https://github.com/Minidoracat/mcp-feedback-enhanced/issues)

## 📄 许可证

MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件

## 📈 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=Minidoracat/mcp-feedback-enhanced&type=Date)](https://star-history.com/#Minidoracat/mcp-feedback-enhanced&Date)

---
**🌟 欢迎点星并分享给更多开发者！**
