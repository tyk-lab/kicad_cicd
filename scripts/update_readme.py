#!/usr/bin/env python3
"""
更新 README.md 中的构建状态徽章
保留原有内容，只更新标记区域
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta


def load_build_results(output_dir: str) -> dict:
    """加载构建结果"""
    output_path = Path(output_dir)
    results = {
        "erc": {"status": "unknown", "errors": 0, "warnings": 0},
        "drc": {"status": "unknown", "errors": 0, "warnings": 0},
        "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        + " 北京时间",
    }

    # 读取 ERC 报告
    erc_file = output_path / "erc_report.json"
    if erc_file.exists():
        try:
            with open(erc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                violations = data.get("violations", [])
                errors = sum(1 for v in violations if v.get("severity") == "error")
                warnings = sum(1 for v in violations if v.get("severity") == "warning")

                if errors > 0:
                    results["erc"] = {
                        "status": "failed",
                        "errors": errors,
                        "warnings": warnings,
                    }
                elif warnings > 0:
                    results["erc"] = {
                        "status": "warning",
                        "errors": 0,
                        "warnings": warnings,
                    }
                else:
                    results["erc"] = {"status": "passed", "errors": 0, "warnings": 0}
        except Exception as e:
            print(f"⚠ 无法读取ERC报告: {e}", file=sys.stderr)

    # 读取 DRC 报告
    drc_file = output_path / "drc_report.json"
    if drc_file.exists():
        try:
            with open(drc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                violations = data.get("violations", [])
                errors = sum(1 for v in violations if v.get("severity") == "error")
                warnings = sum(1 for v in violations if v.get("severity") == "warning")

                if errors > 0:
                    results["drc"] = {
                        "status": "failed",
                        "errors": errors,
                        "warnings": warnings,
                    }
                elif warnings > 0:
                    results["drc"] = {
                        "status": "warning",
                        "errors": 0,
                        "warnings": warnings,
                    }
                else:
                    results["drc"] = {"status": "passed", "errors": 0, "warnings": 0}
        except Exception as e:
            print(f"⚠ 无法读取DRC报告: {e}", file=sys.stderr)

    return results


def generate_status_badge(label: str, status: str, errors: int, warnings: int) -> str:
    """生成状态徽章文本"""
    if status == "passed":
        return f"![{label}](https://img.shields.io/badge/{label}-✓_通过-success)"
    elif status == "warning":
        return (
            f"![{label}](https://img.shields.io/badge/{label}-⚠_{warnings}_警告-yellow)"
        )
    elif status == "failed":
        return (
            f"![{label}](https://img.shields.io/badge/{label}-✗_{errors}_错误-critical)"
        )
    else:
        return f"![{label}](https://img.shields.io/badge/{label}-未知-lightgrey)"


def update_readme(readme_path: str, results: dict, build_number: str) -> bool:
    """更新 README.md 文件"""
    readme_file = Path(readme_path)

    if not readme_file.exists():
        print(f"✗ README 文件不存在: {readme_path}", file=sys.stderr)
        return False

    # 读取原始内容
    with open(readme_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 生成新的构建状态区域
    erc_badge = generate_status_badge(
        "ERC",
        results["erc"]["status"],
        results["erc"]["errors"],
        results["erc"]["warnings"],
    )
    drc_badge = generate_status_badge(
        "DRC",
        results["drc"]["status"],
        results["drc"]["errors"],
        results["drc"]["warnings"],
    )

    build_status = "✓ 成功"
    if results["erc"]["status"] == "failed" or results["drc"]["status"] == "failed":
        build_status = "✗ 失败"
    elif results["erc"]["status"] == "warning" or results["drc"]["status"] == "warning":
        build_status = "⚠ 警告"

    new_status_section = f"""<!-- BUILD_STATUS_START -->
## 📊 最新构建状态

**构建 #{build_number}** | **状态: {build_status}** | **时间: {results['timestamp']}**

{erc_badge} {drc_badge}

<details>
<summary>📋 详细报告</summary>

### ERC 检查
- **状态**: {results['erc']['status'].upper()}
- **错误**: {results['erc']['errors']} 个
- **警告**: {results['erc']['warnings']} 个

### DRC 检查
- **状态**: {results['drc']['status'].upper()}
- **错误**: {results['drc']['errors']} 个
- **警告**: {results['drc']['warnings']} 个

</details>

<!-- BUILD_STATUS_END -->"""

    # 查找并替换标记区域
    start_marker = "<!-- BUILD_STATUS_START -->"
    end_marker = "<!-- BUILD_STATUS_END -->"

    if start_marker in content and end_marker in content:
        # 替换现有区域
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker) + len(end_marker)
        new_content = content[:start_idx] + new_status_section + content[end_idx:]
        print("✓ 更新现有构建状态区域")
    else:
        # 在第一个 ## 标题之前插入
        lines = content.split("\n")
        insert_idx = 0

        # 跳过顶部的标题和徽章
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                insert_idx = i
                break

        if insert_idx > 0:
            lines.insert(insert_idx, "\n" + new_status_section + "\n")
            new_content = "\n".join(lines)
            print("✓ 插入新的构建状态区域")
        else:
            # 如果找不到合适位置，追加到文件末尾
            new_content = content + "\n\n" + new_status_section + "\n"
            print("✓ 追加构建状态到文件末尾")

    # 写入更新后的内容
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✓ README 已更新: {readme_path}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="更新 README 中的构建状态")
    parser.add_argument(
        "-o", "--output", default="outputs", help="输出目录 (默认: outputs)"
    )
    parser.add_argument(
        "-r", "--readme", default="README.md", help="README 文件路径 (默认: README.md)"
    )
    parser.add_argument("-b", "--build-number", default="0", help="构建编号 (默认: 0)")

    args = parser.parse_args()

    print("=" * 60)
    print("更新 README 构建状态")
    print("=" * 60)

    # 加载构建结果
    results = load_build_results(args.output)
    print(f"\n构建结果:")
    print(f"  ERC: {results['erc']['status']}")
    print(f"  DRC: {results['drc']['status']}")
    print(f"  时间: {results['timestamp']}")

    # 更新 README
    success = update_readme(args.readme, results, args.build_number)

    if success:
        print("\n✓ README 更新成功")
        sys.exit(0)
    else:
        print("\n✗ README 更新失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
