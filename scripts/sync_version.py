#!/usr/bin/env python3
"""
版本同步脚本
============

确保项目中所有文件的版本号都与统一版本源保持一致。

使用方式：
    python scripts/sync_version.py [--check-only]

参数：
    --check-only: 只检查版本一致性，不进行修改

作者: jayzqj
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


def get_main_version() -> str:
    """从统一版本文件获取主版本号"""
    version_file = Path("src/mcp_feedback_enhanced/_version.py")
    if not version_file.exists():
        raise FileNotFoundError("统一版本文件不存在: src/mcp_feedback_enhanced/_version.py")
    
    content = version_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("无法从统一版本文件中提取版本号")
    
    return match.group(1)


def check_and_update_file(file_path: Path, pattern: str, replacement: str, version: str, check_only: bool = False) -> Tuple[bool, str]:
    """检查并更新文件中的版本号"""
    if not file_path.exists():
        return False, f"文件不存在: {file_path}"
    
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        
        # 替换版本号
        new_content = re.sub(pattern, replacement.format(version=version), content)
        
        if original_content == new_content:
            return True, f"✅ {file_path}: 版本号已是最新"
        
        if check_only:
            return False, f"❌ {file_path}: 版本号需要更新"
        
        # 写入更新后的内容
        file_path.write_text(new_content, encoding="utf-8")
        return True, f"🔄 {file_path}: 版本号已更新"
        
    except Exception as e:
        return False, f"❌ {file_path}: 处理失败 - {e}"


def sync_versions(check_only: bool = False) -> bool:
    """同步所有文件的版本号"""
    try:
        main_version = get_main_version()
        print(f"📦 主版本号: {main_version}")
        print()
        
        # 定义需要同步的文件和模式
        files_to_sync = [
            {
                "path": Path("pyproject.toml"),
                "pattern": r'version\s*=\s*["\'][^"\']+["\']',
                "replacement": 'version = "{version}"'
            },
            {
                "path": Path("src-tauri/tauri.conf.json"),
                "pattern": r'"version":\s*"[^"]+"',
                "replacement": '"version": "{version}"'
            },
            {
                "path": Path("src-tauri/Cargo.toml"),
                "pattern": r'version\s*=\s*"[^"]+"',
                "replacement": 'version = "{version}"'
            }
        ]
        
        all_success = True
        results = []
        
        for file_info in files_to_sync:
            success, message = check_and_update_file(
                file_info["path"],
                file_info["pattern"],
                file_info["replacement"],
                main_version,
                check_only
            )
            results.append(message)
            if not success:
                all_success = False
        
        # 打印结果
        for result in results:
            print(result)
        
        print()
        if check_only:
            if all_success:
                print("✅ 所有文件版本号都是最新的")
            else:
                print("❌ 发现版本号不一致，请运行 'python scripts/sync_version.py' 进行同步")
        else:
            if all_success:
                print("🎉 版本号同步完成！")
            else:
                print("⚠️ 部分文件同步失败，请检查错误信息")
        
        return all_success
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本同步脚本")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只检查版本一致性，不进行修改"
    )
    
    args = parser.parse_args()
    
    print("🔧 版本同步脚本")
    print("=" * 50)
    
    success = sync_versions(check_only=args.check_only)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
