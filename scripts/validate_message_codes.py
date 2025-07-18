#!/usr/bin/env python3
"""
消息代码验证脚本

验证后端消息代码、前端常量和翻译文件的一致性。
确保所有消息代码都有对应的定义和翻译。

使用方式：
    python scripts/validate_message_codes.py
"""

import json
import re
import sys
from pathlib import Path


def extract_backend_codes():
    """从后端 Python 文件中提取所有消息代码"""
    codes = set()

    # 读取 MessageCodes 类别
    message_codes_file = Path(
        "src/mcp_feedback_enhanced/web/constants/message_codes.py"
    )
    if message_codes_file.exists():
        content = message_codes_file.read_text(encoding="utf-8")
        # 匹配形如 SESSION_FEEDBACK_SUBMITTED = "session.feedbackSubmitted"
        pattern = r'([A-Z_]+)\s*=\s*"([^"]+)"'
        matches = re.findall(pattern, content)
        for constant_name, code in matches:
            codes.add(code)

    return codes


def extract_frontend_codes():
    """从前端 JavaScript 文件中提取所有消息代码"""
    codes = set()

    # 读取 message-codes.js
    message_codes_js = Path(
        "src/mcp_feedback_enhanced/web/static/js/modules/constants/message-codes.js"
    )
    if message_codes_js.exists():
        content = message_codes_js.read_text(encoding="utf-8")
        # 匹配形如 FEEDBACK_SUBMITTED: 'session.feedbackSubmitted'
        pattern = r'[A-Z_]+:\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(pattern, content)
        codes.update(matches)

    # 读取 utils.js 中的 fallback 消息
    utils_js = Path("src/mcp_feedback_enhanced/web/static/js/modules/utils.js")
    if utils_js.exists():
        content = utils_js.read_text(encoding="utf-8")
        # 匹配 fallbackMessages 对象中的 key
        fallback_section = re.search(
            r"fallbackMessages\s*=\s*\{([^}]+)\}", content, re.DOTALL
        )
        if fallback_section:
            pattern = r'[\'"]([^\'"]+)[\'"]:\s*[\'"][^\'"]+[\'"]'
            matches = re.findall(pattern, fallback_section.group(1))
            codes.update(matches)

    return codes


def extract_translation_keys(locale="zh-CN"):
    """从翻译文件中提取所有 key"""
    keys = set()

    translation_file = Path(
        f"src/mcp_feedback_enhanced/web/locales/{locale}/translation.json"
    )
    if translation_file.exists():
        try:
            data = json.loads(translation_file.read_text(encoding="utf-8"))

            def extract_keys_recursive(obj, prefix=""):
                """递归提取所有 key"""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            extract_keys_recursive(value, full_key)
                        else:
                            keys.add(full_key)

            extract_keys_recursive(data)
        except json.JSONDecodeError as e:
            print(f"❌ 无法解析翻译文件 {translation_file}: {e}")

    return keys


def validate_message_codes():
    """执行验证"""
    print("🔍 开始验证消息代码一致性...\n")

    # 提取所有代码
    backend_codes = extract_backend_codes()
    frontend_codes = extract_frontend_codes()

    # 提取所有语言的翻译 key
    locales = ["zh-CN"]
    translation_keys = {}
    for locale in locales:
        translation_keys[locale] = extract_translation_keys(locale)

    # 统计信息
    print("📊 统计信息：")
    print(f"  - 后端消息代码数量: {len(backend_codes)}")
    print(f"  - 前端消息代码数量: {len(frontend_codes)}")
    for locale in locales:
        print(f"  - {locale} 翻译 key 数量: {len(translation_keys[locale])}")
    print()

    # 验证后端代码是否都有前端定义
    print("🔍 检查后端代码是否都有前端定义...")
    missing_in_frontend = backend_codes - frontend_codes
    if missing_in_frontend:
        print("❌ 以下后端代码在前端没有定义:")
        for code in sorted(missing_in_frontend):
            print(f"   - {code}")
    else:
        print("✅ 所有后端代码都有前端定义")
    print()

    # 验证前端代码是否都有翻译
    print("🔍 检查前端代码是否都有翻译...")
    all_frontend_codes = backend_codes | frontend_codes

    for locale in locales:
        print(f"\n  检查 {locale} 翻译:")
        missing_translations = set()

        for code in all_frontend_codes:
            if code not in translation_keys[locale]:
                missing_translations.add(code)

        if missing_translations:
            print("  ❌ 缺少以下翻译:")
            for code in sorted(missing_translations):
                print(f"     - {code}")
        else:
            print("  ✅ 所有代码都有翻译")

    # 检查是否有多余的翻译
    print("\n🔍 检查是否有多余的翻译...")
    for locale in locales:
        # 过滤掉非消息代码的 key（如 buttons, labels 等）
        message_keys = {
            k
            for k in translation_keys[locale]
            if any(
                k.startswith(prefix)
                for prefix in [
                    "system.",
                    "session.",
                    "settings.",
                    "error.",
                    "command.",
                    "file.",
                    "prompt.",
                    "notification.",
                ]
            )
        }

        extra_translations = message_keys - all_frontend_codes
        if extra_translations:
            print(f"\n  {locale} 有多余的翻译:")
            for key in sorted(extra_translations):
                print(f"     - {key}")

    print("\n✅ 验证完成！")

    # 返回是否有错误
    return len(missing_in_frontend) == 0 and all(
        len(
            [
                code
                for code in all_frontend_codes
                if code not in translation_keys[locale]
            ]
        )
        == 0
        for locale in locales
    )


if __name__ == "__main__":
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    import os

    os.chdir(project_root)

    # 执行验证
    success = validate_message_codes()
    sys.exit(0 if success else 1)
