#!/usr/bin/env python3
"""
GitHub Actions 工作流程验证脚本

此脚本验证 GitHub Actions 工作流程文件的语法和配置正确性。
"""

import sys
from pathlib import Path

import yaml


def validate_yaml_syntax(file_path: Path) -> bool:
    """验证 YAML 文件语法"""
    try:
        with open(file_path, encoding="utf-8") as f:
            yaml.safe_load(f)
        print(f"✅ {file_path.name}: YAML 语法正确")
        return True
    except yaml.YAMLError as e:
        print(f"❌ {file_path.name}: YAML 语法错误 - {e}")
        return False
    except Exception as e:
        print(f"❌ {file_path.name}: 读取文件失败 - {e}")
        return False


def validate_workflow_structure(file_path: Path) -> bool:
    """验证工作流程结构"""
    try:
        with open(file_path, encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        # 检查是否成功解析
        if workflow is None:
            print(f"❌ {file_path.name}: 文件为空或解析失败")
            return False

        # 检查必需的顶级字段
        # 注意：YAML 会将 'on' 解析为 True，所以我们需要特殊处理
        required_fields = ["name", "jobs"]
        for field in required_fields:
            if field not in workflow:
                print(f"❌ {file_path.name}: 缺少必需字段 '{field}'")
                print(f"   实际字段: {list(workflow.keys())}")
                return False

        # 检查 'on' 字段（可能被解析为 True）
        if "on" not in workflow and True not in workflow:
            print(f"❌ {file_path.name}: 缺少触发条件 'on'")
            print(f"   实际字段: {list(workflow.keys())}")
            return False

        # 检查 jobs 结构
        if not isinstance(workflow["jobs"], dict):
            print(f"❌ {file_path.name}: 'jobs' 必须是字典")
            return False

        if not workflow["jobs"]:
            print(f"❌ {file_path.name}: 'jobs' 不能为空")
            return False

        print(f"✅ {file_path.name}: 工作流程结构正确")
        return True

    except Exception as e:
        print(f"❌ {file_path.name}: 结构验证失败 - {e}")
        return False


def validate_build_desktop_workflow(file_path: Path) -> bool:
    """验证桌面构建工作流程的特定配置"""
    try:
        with open(file_path, encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        # 检查 matrix 配置
        build_job = workflow["jobs"].get("build-desktop", {})
        strategy = build_job.get("strategy", {})
        matrix = strategy.get("matrix", {})

        if "include" not in matrix:
            print(f"❌ {file_path.name}: 缺少 matrix.include 配置")
            return False

        # 检查平台配置
        platforms = matrix["include"]
        expected_platforms = {"windows", "macos-intel", "macos-arm64", "linux"}
        actual_platforms = {item.get("name") for item in platforms}

        if not expected_platforms.issubset(actual_platforms):
            missing = expected_platforms - actual_platforms
            print(f"❌ {file_path.name}: 缺少平台配置: {missing}")
            return False

        print(f"✅ {file_path.name}: 桌面构建配置正确")
        return True

    except Exception as e:
        print(f"❌ {file_path.name}: 桌面构建验证失败 - {e}")
        return False


def validate_publish_workflow(file_path: Path) -> bool:
    """验证发布工作流程的特定配置"""
    try:
        with open(file_path, encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        # 检查输入参数 - 注意 'on' 可能被解析为 True
        on_section = workflow.get("on") or workflow.get(True)
        if not on_section:
            print(f"❌ {file_path.name}: 找不到触发条件")
            return False

        workflow_dispatch = on_section.get("workflow_dispatch", {})
        inputs = workflow_dispatch.get("inputs", {})

        required_inputs = {"version_type", "include_desktop"}
        actual_inputs = set(inputs.keys())

        if not required_inputs.issubset(actual_inputs):
            missing = required_inputs - actual_inputs
            print(f"❌ {file_path.name}: 缺少输入参数: {missing}")
            print(f"   实际输入参数: {actual_inputs}")
            return False

        # 检查是否有桌面应用处理步骤
        release_job = workflow["jobs"].get("release", {})
        steps = release_job.get("steps", [])

        has_desktop_steps = any(
            "desktop" in step.get("name", "").lower() for step in steps
        )

        if not has_desktop_steps:
            print(f"❌ {file_path.name}: 缺少桌面应用处理步骤")
            return False

        print(f"✅ {file_path.name}: 发布工作流程配置正确")
        return True

    except Exception as e:
        print(f"❌ {file_path.name}: 发布工作流程验证失败 - {e}")
        return False


def main():
    """主函数"""
    print("🔍 验证 GitHub Actions 工作流程...")
    print()

    # 获取工作流程目录
    workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"

    if not workflows_dir.exists():
        print(f"❌ 工作流程目录不存在: {workflows_dir}")
        sys.exit(1)

    # 查找所有工作流程文件
    workflow_files = list(workflows_dir.glob("*.yml")) + list(
        workflows_dir.glob("*.yaml")
    )

    if not workflow_files:
        print(f"❌ 在 {workflows_dir} 中没有找到工作流程文件")
        sys.exit(1)

    print(f"📁 找到 {len(workflow_files)} 个工作流程文件")
    print()

    # 验证每个文件
    all_valid = True

    for workflow_file in sorted(workflow_files):
        print(f"🔍 验证 {workflow_file.name}...")

        # 基本语法验证
        if not validate_yaml_syntax(workflow_file):
            all_valid = False
            continue

        # 结构验证
        if not validate_workflow_structure(workflow_file):
            all_valid = False
            continue

        # 特定工作流程验证
        if workflow_file.name == "build-desktop.yml":
            if not validate_build_desktop_workflow(workflow_file):
                all_valid = False
        elif workflow_file.name == "publish.yml":
            if not validate_publish_workflow(workflow_file):
                all_valid = False

        print()

    # 总结
    if all_valid:
        print("🎉 所有工作流程文件验证通过！")
        print()
        print("📋 下一步:")
        print("  1. 提交并推送更改到 GitHub")
        print("  2. 测试 'Build Desktop Applications' 工作流程")
        print("  3. 测试 'Build Desktop & Release' 工作流程")
        print("  4. 验证桌面应用是否正确包含在发布中")
    else:
        print("❌ 部分工作流程文件验证失败")
        print("请修复上述问题后重新运行验证")
        sys.exit(1)


if __name__ == "__main__":
    main()
