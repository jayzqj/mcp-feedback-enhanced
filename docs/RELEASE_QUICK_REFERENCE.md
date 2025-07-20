# 🚀 发布流程快速参考

## ⚡ 一键发布 (推荐)

```bash
# 1. 访问 GitHub Actions
https://github.com/jayzqj/mcp-feedback-enhanced/actions/workflows/publish.yml

# 2. 点击 "Run workflow"
# 3. 选择版本类型: patch/minor/major 或自定义版本
# 4. 选择是否包含桌面应用: true/false
# 5. 点击 "Run workflow"
```

## 🛠️ 本地发布

### 快速命令

```bash
# 版本更新
python scripts/release.py patch    # Bug修复
python scripts/release.py minor    # 新功能  
python scripts/release.py major    # 重大更改

# 构建和发布
python scripts/cleanup_cache.py --clean
uv build
uv run twine check dist/*
uv publish --token YOUR_PYPI_TOKEN
```

### 完整流程

```bash
# 1. 准备
uv sync --dev
uv run ruff format && uv run ruff check
uv run pytest

# 2. 版本
python scripts/release.py patch

# 3. 构建
python scripts/cleanup_cache.py --clean
uv build

# 4. 验证
uv run twine check dist/*

# 5. 发布
uv publish --token YOUR_PYPI_TOKEN

# 6. 标签
git push origin main
git push origin "v$(grep '^version =' pyproject.toml | cut -d'"' -f2)"
```

## 📋 发布检查清单

### 发布前 ✅
- [ ] 代码检查: `uv run ruff check`
- [ ] 测试通过: `uv run pytest`
- [ ] 文档更新: `CHANGELOG.md`
- [ ] 版本确定: `patch/minor/major`

### 发布后 ✅
- [ ] PyPI可用: `uvx ai-interactive-feedback@latest --help`
- [ ] 功能正常: `uvx ai-interactive-feedback@latest test`
- [ ] 文档同步: 检查README版本

## 🔧 常用命令

```bash
# 检查当前版本
grep '^version =' pyproject.toml

# 测试安装
uvx ai-interactive-feedback@latest --help

# 检查包大小
ls -lh dist/

# 清理缓存
python scripts/cleanup_cache.py --clean

# 本地测试桌面应用
python scripts/build_desktop.py --release
```

## 🚨 紧急修复

```bash
# 1. 创建热修复分支
git checkout -b hotfix/fix-name

# 2. 修复并测试
# ... 修复代码
uv run pytest tests/critical/

# 3. 快速发布
python scripts/release.py patch
# 使用 GitHub Actions 发布

# 4. 合并回主分支
git checkout main
git merge hotfix/fix-name
```

## 📊 版本策略

| 类型 | 何时使用 | 示例 |
|------|----------|------|
| `patch` | Bug修复、文档更新 | 2.6.0 → 2.6.1 |
| `minor` | 新功能、改进 | 2.6.0 → 2.7.0 |
| `major` | 破坏性更改 | 2.6.0 → 3.0.0 |
| `custom` | 特殊版本 | 2025.0720.01 |

## 🔗 重要链接

- **GitHub Actions**: [发布工作流程](https://github.com/jayzqj/mcp-feedback-enhanced/actions/workflows/publish.yml)
- **PyPI页面**: [ai-interactive-feedback](https://pypi.org/project/ai-interactive-feedback/)
- **详细文档**: [完整发布指南](./RELEASE_GUIDE.md)

## 🆘 故障排除

| 问题 | 解决方案 |
|------|----------|
| 认证失败 | 检查 `PYPI_API_TOKEN` |
| 版本冲突 | 更新版本号 |
| 构建失败 | 检查依赖和代码 |
| 桌面应用缺失 | 重新构建或跳过 |

---

**快速参考版本**: v1.0  
**对应详细文档**: [RELEASE_GUIDE.md](./RELEASE_GUIDE.md)
