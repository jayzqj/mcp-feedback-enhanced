#!/usr/bin/env python3
"""
本地发布脚本
用法：
  python scripts/release.py patch   # 2.0.0 -> 2.0.1
  python scripts/release.py minor   # 2.0.0 -> 2.1.0
  python scripts/release.py major   # 2.0.0 -> 3.0.0
"""

import re
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, check=True):
    """执行命令并返回结果"""
    print(f"🔨 执行: {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        print(f"❌ 错误: {result.stderr}")
        sys.exit(1)
    return result


def get_current_version():
    """从 pyproject.toml 获取当前版本"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("无法找到版本号")


def bump_version(version_type):
    """更新版本号"""
    if version_type not in ["patch", "minor", "major"]:
        print("❌ 版本类型必须是: patch, minor, major")
        sys.exit(1)

    current = get_current_version()
    print(f"📦 当前版本: {current}")

    # 使用 bump2version with allow-dirty
    run_cmd(f"uv run bump2version --allow-dirty {version_type}")

    new_version = get_current_version()
    print(f"🎉 新版本: {new_version}")

    return current, new_version


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    version_type = sys.argv[1]

    print("🚀 开始发布流程...")

    # 检查 Git 状态（仅提示，不阻止）
    result = run_cmd("git status --porcelain", check=False)
    if result.stdout.strip():
        print("⚠️  有未提交的变更：")
        print(result.stdout)
        print("💡 将继续执行（使用 --allow-dirty 模式）")

    # 更新版本
    old_version, new_version = bump_version(version_type)

    # 构建套件
    print("📦 构建套件...")
    run_cmd("uv build")

    # 检查套件
    print("🔍 检查套件...")
    run_cmd("uv run twine check dist/*")

    # 提交所有变更（包括版本更新）
    print("💾 提交版本更新...")
    run_cmd("git add .")
    run_cmd(f'git commit -m "🔖 Release v{new_version}"')
    run_cmd(f'git tag "v{new_version}"')

    # 询问是否发布
    print(f"\n✅ 准备发布版本 {old_version} -> {new_version}")
    choice = input("是否发布到 PyPI？ (y/N): ")

    if choice.lower() == "y":
        print("🚀 发布到 PyPI...")
        run_cmd("uv run twine upload dist/*")

        print("📤 推送到 GitHub...")
        run_cmd("git push origin main")
        run_cmd(f'git push origin "v{new_version}"')

        print(f"🎉 发布完成！版本 v{new_version} 已上线")
        print("📦 安装命令: uvx mcp-feedback-enhanced")
    else:
        print("⏸️  发布已取消，版本已更新但未发布")
        print("💡 您可以稍后手动发布: uv run twine upload dist/*")


if __name__ == "__main__":
    main()
