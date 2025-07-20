# v2025.0720.03 Release Notes

## 🖥️ Desktop Application Window Optimization

### ✨ New Features

#### Smart Window Sizing
- **Full Screen Height**: Desktop application window height automatically adapts to screen height
- **Reasonable Width Ratio**: Width maintains reasonable proportions (max 1400px or 75% of screen width)
- **Cross-Resolution Compatibility**: Automatically adapts to 1080p, 1440p, 4K and other screen resolutions

#### Centered Display
- **Default Centering**: Window automatically centers on screen at startup
- **Visual Enhancement**: Provides better visual experience and user-friendliness
- **Remains Adjustable**: Users can still manually adjust window size and position

#### Unified Branding
- **Consistent Naming**: Application title changed from "MCP Feedback Enhanced" to "AI Interactive Feedback"
- **Multi-language Sync**: All language versions have synchronized title updates
- **Brand Consistency**: Provides more consistent brand experience

### 🔧 Technical Improvements

#### Dynamic Screen Detection
- **Real-time Detection**: Automatically detects primary monitor size at startup
- **Smart Calculation**: Dynamically calculates optimal window size and position
- **Multi-monitor Support**: Correctly identifies primary display

#### Configuration Optimization
- **Tauri Configuration**: Updated desktop application configuration files
- **Rust Code**: Enhanced window management logic
- **Logging Output**: Provides detailed window setup information

### 📐 Window Size Examples

| Screen Resolution | Window Size | Window Position | Description |
|-------------------|-------------|-----------------|-------------|
| 1920×1080 | 1400×1080 | (260, 0) | Horizontally centered, vertically full |
| 2560×1440 | 1400×1440 | (580, 0) | Horizontally centered, vertically full |
| 1366×768 | 1024×768 | (171, 0) | Horizontally centered, vertically full |
| 3840×2160 | 1400×2160 | (1220, 0) | Horizontally centered, vertically full |

### 🔄 Upgrade Instructions

#### Desktop Application Users
- Need to rebuild or download new version of desktop application
- New version will automatically apply optimized window settings

#### Web UI Users
- Title updates will take effect after service restart
- No additional actions required

### 📝 Complete Change List

#### Configuration File Updates
- `src-tauri/tauri.conf.json`: Updated product name and window title
- `src/mcp_feedback_enhanced/web/locales/*/translation.json`: Updated multi-language titles
- `src/mcp_feedback_enhanced/web/routes/main_routes.py`: Updated page titles

#### Code Updates
- `src-tauri/src/main.rs`: Added smart window sizing and centering logic
- `src/mcp_feedback_enhanced/web/static/js/app.js`: Updated dynamic title setting
- `src/mcp_feedback_enhanced/web/templates/`: Updated HTML template titles

#### Version Number Updates
- `pyproject.toml`: 2025.0720.02 → 2025.0720.03
- `src/mcp_feedback_enhanced/__init__.py`: Synchronized version number update
- All related configuration files unified version number update

---

**Installation**:
```bash
# Upgrade to latest version
uvx ai-interactive-feedback@latest

# Or specify version
uvx ai-interactive-feedback@2025.0720.03
```

**Test Commands**:
```bash
# Test desktop application (see new window optimization)
uvx ai-interactive-feedback@2025.0720.03 test --desktop

# Test Web UI (see new title)
uvx ai-interactive-feedback@2025.0720.03 test --web
```
