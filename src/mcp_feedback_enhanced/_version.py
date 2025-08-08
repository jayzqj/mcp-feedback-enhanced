#!/usr/bin/env python3
"""
统一版本管理模块
================

这是项目的单一版本源文件，所有其他文件都应该从这里导入版本号。

版本格式: YYYY.MMDD.PATCH
- YYYY: 年份
- MMDD: 月日 (4位数，如0808表示8月8日)
- PATCH: 补丁版本号

作者: jayzqj
"""

# 项目版本号 - 单一真实源
__version__ = "2025.808.2"

# 项目元信息
__author__ = "jayzqj"
__email__ = ""
__description__ = "Enhanced AI interactive feedback server with Web UI support"
__url__ = "https://github.com/jayzqj/mcp-feedback-enhanced"

# 导出版本信息
def get_version():
    """获取当前版本号"""
    return __version__

def get_version_info():
    """获取详细版本信息"""
    return {
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
        "url": __url__,
    }

# 版本兼容性检查
def check_version_compatibility(required_version: str) -> bool:
    """检查版本兼容性"""
    try:
        current_parts = [int(x) for x in __version__.split('.')]
        required_parts = [int(x) for x in required_version.split('.')]
        
        # 主版本必须匹配
        if current_parts[0] != required_parts[0]:
            return False
            
        # 次版本必须大于等于要求的版本
        if len(current_parts) >= 2 and len(required_parts) >= 2:
            if current_parts[1] < required_parts[1]:
                return False
                
        return True
    except (ValueError, IndexError):
        return False
