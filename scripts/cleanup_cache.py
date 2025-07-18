#!/usr/bin/env python3
"""
UV Cache 清理脚本
================

定期清理 uv cache 以防止磁盘空间不断增加
特别针对 Windows 系统「文件正由另一个程序使用」的问题提供解决方案

使用方式：
  python scripts/cleanup_cache.py --size       # 查看 cache 大小和详细信息
  python scripts/cleanup_cache.py --dry-run    # 预览将要清理的内容（不实际清理）
  python scripts/cleanup_cache.py --clean      # 执行标准清理
  python scripts/cleanup_cache.py --force      # 强制清理（会尝试关闭相关程序）

功能特色：
  - 智能跳过正在使用中的文件
  - 提供强制清理模式
  - 详细的清理统计和进度显示
  - 支持 Windows/macOS/Linux 跨平台
"""

import argparse
import os
import subprocess
from pathlib import Path


def get_cache_dir():
    """获取 uv cache 目录"""
    # Windows 默认路径
    if os.name == "nt":
        return Path.home() / "AppData" / "Local" / "uv"
    # macOS/Linux 默认路径
    return Path.home() / ".cache" / "uv"


def get_cache_size(cache_dir):
    """计算 cache 目录大小"""
    if not cache_dir.exists():
        return 0

    total_size = 0
    for dirpath, dirnames, filenames in os.walk(cache_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def run_uv_command(command, check=True):
    """執行 uv 命令"""
    try:
        result = subprocess.run(
            ["uv"] + command, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令執行失敗: uv {' '.join(command)}")
        print(f"錯誤: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ 找不到 uv 命令，请确认 uv 已正确安装")
        return None


def show_cache_info():
    """显示 cache 信息"""
    print("🔍 UV Cache 信息")
    print("=" * 50)

    cache_dir = get_cache_dir()
    print(f"Cache 目录: {cache_dir}")

    if cache_dir.exists():
        cache_size = get_cache_size(cache_dir)
        print(f"Cache 大小: {format_size(cache_size)}")

        # 显示子目录大小
        subdirs = []
        for subdir in cache_dir.iterdir():
            if subdir.is_dir():
                subdir_size = get_cache_size(subdir)
                subdirs.append((subdir.name, subdir_size))

        if subdirs:
            print("\n📁 子目录大小:")
            subdirs.sort(key=lambda x: x[1], reverse=True)
            for name, size in subdirs[:10]:  # 显示前10大
                print(f"  {name}: {format_size(size)}")
    else:
        print("Cache 目录不存在")


def clean_cache_selective(cache_dir, dry_run=False):
    """选择性清理 cache，跳过正在使用的文件"""
    cleaned_count = 0
    skipped_count = 0
    total_saved = 0

    print(f"🔍 扫描 cache 目录: {cache_dir}")

    # 遍历 cache 目录
    for root, dirs, files in os.walk(cache_dir):
        # 跳过一些可能正在使用的目录
        if any(skip_dir in root for skip_dir in ["Scripts", "Lib", "pyvenv.cfg"]):
            continue

        for file in files:
            file_path = Path(root) / file
            try:
                if dry_run:
                    file_size = file_path.stat().st_size
                    total_saved += file_size
                    cleaned_count += 1
                    if cleaned_count <= 10:  # 只显示前10个
                        print(
                            f"  将清理: {file_path.relative_to(cache_dir)} ({format_size(file_size)})"
                        )
                else:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    total_saved += file_size
                    cleaned_count += 1
            except (OSError, PermissionError, FileNotFoundError):
                skipped_count += 1
                if not dry_run and skipped_count <= 5:  # 只显示前5个错误
                    print(f"  ⚠️  跳过: {file_path.name} (正在使用中)")

    return cleaned_count, skipped_count, total_saved


def clean_cache(dry_run=False):
    """清理 cache"""
    action = "预览" if dry_run else "执行"
    print(f"🧹 {action} UV Cache 清理")
    print("=" * 50)

    # 显示清理前的大小
    cache_dir = get_cache_dir()
    if cache_dir.exists():
        before_size = get_cache_size(cache_dir)
        print(f"清理前大小: {format_size(before_size)}")
    else:
        print("Cache 目录不存在，无需清理")
        return

    if dry_run:
        print("\n🔍 将要清理的内容:")
        # 先尝试 uv cache clean --dry-run
        result = run_uv_command(["cache", "clean", "--dry-run"], check=False)
        if result and result.returncode == 0:
            print(result.stdout)
        else:
            print("  使用自定义扫描...")
            cleaned_count, skipped_count, total_saved = clean_cache_selective(
                cache_dir, dry_run=True
            )
            print("\n📊 预览结果:")
            print(f"  可清理文件: {cleaned_count}")
            print(f"  预计节省: {format_size(total_saved)}")
    else:
        print("\n🗑️  正在清理...")

        # 先尝试标准清理
        result = run_uv_command(["cache", "clean"], check=False)
        if result and result.returncode == 0:
            print("✅ 标准 Cache 清理完成")
        else:
            print("⚠️  标准清理失败，使用选择性清理...")
            cleaned_count, skipped_count, total_saved = clean_cache_selective(
                cache_dir, dry_run=False
            )

            print("\n📊 清理结果:")
            print(f"  已清理文件: {cleaned_count}")
            print(f"  跳过文件: {skipped_count}")
            print(f"  节省空间: {format_size(total_saved)}")

            if skipped_count > 0:
                print(f"\n💡 提示: {skipped_count} 个文件正在使用中，已跳过")
                print("   建议关闭相关程序后重新执行清理")

        # 显示清理后的大小
        if cache_dir.exists():
            after_size = get_cache_size(cache_dir)
            saved_size = before_size - after_size
            print("\n📈 总体效果:")
            print(f"  清理前: {format_size(before_size)}")
            print(f"  清理后: {format_size(after_size)}")
            print(f"  实际节省: {format_size(saved_size)}")
        else:
            print(f"  节省空间: {format_size(before_size)}")


def force_clean_cache():
    """强制清理 cache（关闭相关程序后）"""
    print("🔥 强制清理模式")
    print("=" * 50)
    print("⚠️  警告：此模式会尝试关闭可能使用 cache 的程序")

    confirm = input("确定要继续吗？(y/N): ")
    if confirm.lower() != "y":
        print("❌ 已取消")
        return

    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        print("Cache 目录不存在")
        return

    before_size = get_cache_size(cache_dir)
    print(f"清理前大小: {format_size(before_size)}")

    # 尝试关闭可能的 uvx 程序
    print("\n🔍 检查相关程序...")
    try:
        import psutil

        killed_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and any(
                    name in proc.info["name"].lower()
                    for name in ["uvx", "uv.exe", "python.exe"]
                ):
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if "mcp-feedback-enhanced" in cmdline or "uvx" in cmdline:
                        print(
                            f"  终止程序: {proc.info['name']} (PID: {proc.info['pid']})"
                        )
                        proc.terminate()
                        killed_processes.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed_processes:
            print(f"  已终止 {len(killed_processes)} 个程序")
            import time

            time.sleep(2)  # 等待程序完全关闭
        else:
            print("  未发现相关程序")

    except ImportError:
        print("  无法检查程序（需要 psutil），继续清理...")

    # 再次尝试标准清理
    print("\n🗑️  执行清理...")
    result = run_uv_command(["cache", "clean"], check=False)
    if result and result.returncode == 0:
        print("✅ 强制清理成功")
    else:
        print("⚠️  标准清理仍然失败，使用文件级清理...")
        cleaned_count, skipped_count, total_saved = clean_cache_selective(
            cache_dir, dry_run=False
        )
        print(f"  清理文件: {cleaned_count}, 跳过: {skipped_count}")

    # 显示结果
    after_size = get_cache_size(cache_dir)
    saved_size = before_size - after_size
    print("\n📈 清理结果:")
    print(f"  节省空间: {format_size(saved_size)}")


def main():
    parser = argparse.ArgumentParser(description="UV Cache 清理工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--size", action="store_true", help="显示 cache 大小信息")
    group.add_argument(
        "--dry-run", action="store_true", help="预览清理内容（不实际清理）"
    )
    group.add_argument("--clean", action="store_true", help="执行 cache 清理")
    group.add_argument(
        "--force", action="store_true", help="强制清理（会尝试关闭相关程序）"
    )

    args = parser.parse_args()

    if args.size:
        show_cache_info()
    elif args.dry_run:
        clean_cache(dry_run=True)
    elif args.clean:
        clean_cache(dry_run=False)
    elif args.force:
        force_clean_cache()


if __name__ == "__main__":
    main()
