#!/usr/bin/env python3
"""
KiCad自动化导出脚本
功能：ERC/DRC检查、导出原理图PDF、BOM、Gerber文件和PCB图像
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any


class KiCadExporter:
    def __init__(
        self, project_path: str, output_dir: str = "outputs", custom_3d_path: str = None
    ):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.stem
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 检测KiCad CLI命令
        self.kicad_cli = self._detect_kicad_cli()

        # 文件路径
        self.sch_file = self.project_path.with_suffix(".kicad_sch")
        self.pcb_file = self.project_path.with_suffix(".kicad_pcb")

        # 结果统计
        self.results = {
            "erc": {"status": "skipped", "violations": 0},
            "drc": {"status": "skipped", "violations": 0},
            "exports": {},
        }

    def _detect_kicad_cli(self) -> str:
        """检测可用的KiCad CLI命令"""
        commands = ["kicad.kicad-cli", "kicad-cli"]

        for cmd in commands:
            try:
                result = subprocess.run(
                    [cmd, "version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    print(f"✓ 检测到KiCad CLI: {cmd}")
                    print(f"  版本: {result.stdout.strip()}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        raise RuntimeError(
            "错误: 未找到KiCad CLI命令 (尝试过: kicad.kicad-cli, kicad-cli)"
        )

    def _run_command(self, args: list, description: str) -> Tuple[bool, str]:
        """运行命令并返回结果"""
        print(f"\n{'='*60}")
        print(f"执行: {description}")
        print(f"命令: {' '.join(args)}")
        print("=" * 60)

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120)

            # 过滤掉 wxWidgets 调试信息
            filtered_stderr = self._filter_wx_debug(result.stderr)

            if result.returncode == 0:
                print(f"✓ {description} - 成功")
                return True, result.stdout
            else:
                # 不打印退出码和错误信息，由调用方根据 JSON 结果判断
                return False, filtered_stderr

        except subprocess.TimeoutExpired:
            print(f"⚠ {description} - 超时")
            return False, "命令执行超时"
        except Exception as e:
            print(f"⚠ {description} - 异常: {str(e)}")
            return False, str(e)

    def _filter_wx_debug(self, stderr: str) -> str:
        """过滤掉 wxWidgets 调试信息"""
        if not stderr:
            return ""

        lines = stderr.split("\n")
        filtered = []

        for line in lines:
            # 过滤掉常见的 wxWidgets 调试信息
            if any(
                pattern in line
                for pattern in [
                    "Adding duplicate image handler",
                    "Debug: Adding duplicate",
                ]
            ):
                continue
            filtered.append(line)

        return "\n".join(filtered).strip()

    def run_erc(self) -> bool:
        """运行ERC检查"""
        if not self.sch_file.exists():
            print(f"⚠ 跳过ERC: 原理图文件不存在 ({self.sch_file})")
            return False

        report_file = self.output_dir / "erc_report.json"

        args = [
            self.kicad_cli,
            "sch",
            "erc",
            "--severity-all",
            "--format",
            "json",
            "--output",
            str(report_file),
            str(self.sch_file),
        ]

        # 不使用 --exit-code-violations，通过 JSON 结果判断
        success, output = self._run_command(args, "ERC检查")

        # 解析结果并统计不同严重级别
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    violations = data.get("violations", [])

                    # 统计不同严重级别
                    errors = sum(1 for v in violations if v.get("severity") == "error")
                    warnings = sum(
                        1 for v in violations if v.get("severity") == "warning"
                    )
                    exclusions = sum(1 for v in violations if v.get("excluded", False))
                    total = len(violations)

                    # 只有错误级别才标记为失败
                    if errors > 0:
                        self.results["erc"] = {
                            "status": "failed",
                            "violations": total,
                            "errors": errors,
                            "warnings": warnings,
                            "exclusions": exclusions,
                        }
                        print(f"  ✗ 发现 {errors} 个错误, {warnings} 个警告")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")
                    elif warnings > 0:
                        self.results["erc"] = {
                            "status": "warning",
                            "violations": total,
                            "errors": 0,
                            "warnings": warnings,
                            "exclusions": exclusions,
                        }
                        print(f"  ⚠ 发现 {warnings} 个警告")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")
                    else:
                        self.results["erc"] = {
                            "status": "passed",
                            "violations": total,
                            "errors": 0,
                            "warnings": 0,
                            "exclusions": exclusions,
                        }
                        print("  ✓ 未发现问题")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")

            except json.JSONDecodeError as e:
                print(f"  ⚠ JSON解析失败: {e}")
                self.results["erc"] = {"status": "error", "violations": "unknown"}

        return True  # ERC运行成功（即使有警告）

    def run_drc(self) -> bool:
        """运行DRC检查"""
        if not self.pcb_file.exists():
            print(f"⚠ 跳过DRC: PCB文件不存在 ({self.pcb_file})")
            return False

        report_file = self.output_dir / "drc_report.json"

        args = [
            self.kicad_cli,
            "pcb",
            "drc",
            "--severity-all",
            "--format",
            "json",
            "--output",
            str(report_file),
            str(self.pcb_file),
        ]

        # 不使用 --exit-code-violations，通过 JSON 结果判断
        success, output = self._run_command(args, "DRC检查")

        # 解析结果并统计不同严重级别
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    violations = data.get("violations", [])

                    # 统计不同严重级别
                    errors = sum(1 for v in violations if v.get("severity") == "error")
                    warnings = sum(
                        1 for v in violations if v.get("severity") == "warning"
                    )
                    exclusions = sum(1 for v in violations if v.get("excluded", False))
                    total = len(violations)

                    # 只有错误级别才标记为失败
                    if errors > 0:
                        self.results["drc"] = {
                            "status": "failed",
                            "violations": total,
                            "errors": errors,
                            "warnings": warnings,
                            "exclusions": exclusions,
                        }
                        print(f"  ✗ 发现 {errors} 个错误, {warnings} 个警告")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")
                    elif warnings > 0:
                        self.results["drc"] = {
                            "status": "warning",
                            "violations": total,
                            "errors": 0,
                            "warnings": warnings,
                            "exclusions": exclusions,
                        }
                        print(f"  ⚠ 发现 {warnings} 个警告")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")
                    else:
                        self.results["drc"] = {
                            "status": "passed",
                            "violations": total,
                            "errors": 0,
                            "warnings": 0,
                            "exclusions": exclusions,
                        }
                        print("  ✓ 未发现问题")
                        if exclusions > 0:
                            print(f"  ℹ {exclusions} 个违规项已排除")

            except json.JSONDecodeError as e:
                print(f"  ⚠ JSON解析失败: {e}")
                self.results["drc"] = {"status": "error", "violations": "unknown"}

        return True  # DRC运行成功（即使有警告）

    def export_schematic_pdf(self) -> bool:
        """导出原理图PDF"""
        if not self.sch_file.exists():
            print(f"⚠ 跳过PDF导出: 原理图文件不存在")
            return False

        output_file = self.output_dir / f"{self.project_name}-Schematic.pdf"

        args = [
            self.kicad_cli,
            "sch",
            "export",
            "pdf",
            "--output",
            str(output_file),
            str(self.sch_file),
        ]

        success, _ = self._run_command(args, "导出原理图PDF")
        self.results["exports"]["schematic_pdf"] = output_file.exists()
        return success

    def export_bom(self) -> bool:
        """导出BOM"""
        if not self.sch_file.exists():
            print(f"⚠ 跳过BOM导出: 原理图文件不存在")
            return False

        output_file = self.output_dir / f"{self.project_name}-BOM.csv"

        args = [
            self.kicad_cli,
            "sch",
            "export",
            "bom",
            "--output",
            str(output_file),
            str(self.sch_file),
        ]

        success, _ = self._run_command(args, "导出BOM")
        self.results["exports"]["bom"] = output_file.exists()
        return success

    def export_gerber(self) -> bool:
        """导出Gerber文件"""
        if not self.pcb_file.exists():
            print(f"⚠ 跳过Gerber导出: PCB文件不存在")
            return False

        gerber_dir = self.output_dir / "gerber"
        gerber_dir.mkdir(exist_ok=True)

        # 导出Gerber层
        args_gerber = [
            self.kicad_cli,
            "pcb",
            "export",
            "gerbers",
            "--output",
            str(gerber_dir) + "/",
            str(self.pcb_file),
        ]

        success1, _ = self._run_command(args_gerber, "导出Gerber层文件")

        # 导出钻孔文件
        args_drill = [
            self.kicad_cli,
            "pcb",
            "export",
            "drill",
            "--format",
            "excellon",
            "--output",
            str(gerber_dir) + "/",
            str(self.pcb_file),
        ]

        success2, _ = self._run_command(args_drill, "导出钻孔文件")

        # 打包ZIP
        if success1 and success2:
            import zipfile

            zip_file = self.output_dir / f"{self.project_name}-Gerber.zip"

            with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in gerber_dir.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(gerber_dir))

            print(f"✓ Gerber文件已打包: {zip_file}")
            self.results["exports"]["gerber_zip"] = zip_file.exists()

        return success1 and success2

    def export_pcb_images(self) -> bool:
        """导出PCB图像"""
        if not self.pcb_file.exists():
            print(f"⚠ 跳过PCB图像导出: PCB文件不存在")
            return False

        all_success = True

        # 导出正面SVG
        front_svg = self.output_dir / f"{self.project_name}-PCB-Front.svg"
        args_front = [
            self.kicad_cli,
            "pcb",
            "export",
            "svg",
            "--output",
            str(front_svg),
            "--layers",
            "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts",
            str(self.pcb_file),
        ]

        success, _ = self._run_command(args_front, "导出PCB正面图像")
        self.results["exports"]["pcb_front_svg"] = front_svg.exists()
        all_success = all_success and success

        # 导出背面SVG
        back_svg = self.output_dir / f"{self.project_name}-PCB-Back.svg"
        args_back = [
            self.kicad_cli,
            "pcb",
            "export",
            "svg",
            "--output",
            str(back_svg),
            "--layers",
            "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts",
            str(self.pcb_file),
        ]

        success, _ = self._run_command(args_back, "导出PCB背面图像")
        self.results["exports"]["pcb_back_svg"] = back_svg.exists()
        all_success = all_success and success

        # 导出3D STEP模型（可选，失败不影响整体结果）
        step_file = self.output_dir / f"{self.project_name}-3D.step"
        args_step = [
            self.kicad_cli,
            "pcb",
            "export",
            "step",
            "--output",
            str(step_file),
            str(self.pcb_file),
        ]

        print(f"\n{'='*60}")
        print("执行: 导出3D STEP模型 (可选)")
        print(f"命令: {' '.join(args_step)}")
        print("=" * 60)

        try:
            # 抑制wxWidgets调试输出
            result = subprocess.run(
                args_step,
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "KICAD_SKIP_ERRORS": "1"},
            )

            if result.returncode == 0 and step_file.exists():
                print("✓ 导出3D STEP模型 - 成功")
                self.results["exports"]["step_3d"] = True
            else:
                print("ℹ 3D STEP模型导出跳过 (元件可能缺少3D模型)")
                self.results["exports"]["step_3d"] = False
                # 删除可能生成的不完整文件
                if step_file.exists():
                    step_file.unlink()
                    print(f"  已清理不完整的STEP文件")

        except Exception as e:
            print(f"ℹ 3D STEP模型导出跳过 ({str(e)})")
            self.results["exports"]["step_3d"] = False
            # 删除可能生成的不完整文件
            if step_file.exists():
                step_file.unlink()

        # 3D导出失败不影响整体成功状态
        return all_success

    def generate_summary(self) -> str:
        """生成构建摘要"""
        from datetime import datetime

        summary = f"""## 构建摘要

**构建时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
**项目名称**: {self.project_name}

### 质量检查

- **ERC (电气规则检查)**: {self._format_check_status('erc')}
- **DRC (设计规则检查)**: {self._format_check_status('drc')}

### 导出文件

"""

        exports = [
            ("schematic_pdf", "Schematic PDF", True),
            ("bom", "BOM (Bill of Materials)", True),
            ("gerber_zip", "Gerber files (ZIP)", True),
            ("pcb_front_svg", "PCB Front Image (SVG)", True),
            ("pcb_back_svg", "PCB Back Image (SVG)", True),
            ("step_3d", "3D STEP Model", False),  # 可选
        ]

        for key, name, required in exports:
            exported = self.results["exports"].get(key, False)
            if exported:
                summary += f"- ✓ {name}\n"
            elif required:
                summary += f"- ✗ {name}\n"
            else:
                summary += f"- ℹ {name} (可选，已跳过)\n"

        return summary

    def _format_check_status(self, check_type: str) -> str:
        """格式化检查状态"""
        result = self.results[check_type]
        status = result["status"]

        if status == "passed":
            exclusions = result.get("exclusions", 0)
            if exclusions > 0:
                return f"✓ 通过 ({exclusions} 项已排除)"
            return "✓ 通过"
        elif status == "warning":
            warnings = result.get("warnings", 0)
            exclusions = result.get("exclusions", 0)
            text = f"⚠ {warnings} 个警告"
            if exclusions > 0:
                text += f" ({exclusions} 项已排除)"
            return text
        elif status == "failed":
            errors = result.get("errors", 0)
            warnings = result.get("warnings", 0)
            exclusions = result.get("exclusions", 0)
            text = f"✗ 失败 ({errors} 个错误"
            if warnings > 0:
                text += f", {warnings} 个警告"
            if exclusions > 0:
                text += f", {exclusions} 项已排除"
            text += ")"
            return text
        elif status == "error":
            return "✗ 检查错误"
        else:
            return "- 跳过"

    def save_summary(self):
        """保存构建摘要"""
        summary = self.generate_summary()
        summary_file = self.output_dir / "build_summary.md"

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"\n✓ 构建摘要已保存: {summary_file}")
        print("\n" + summary)

    def run_all(self, skip_checks=False, skip_exports=False):
        """运行所有任务"""
        print("=" * 60)
        print("KiCad 自动化导出工具")
        print("=" * 60)
        print(f"项目: {self.project_name}")
        print(f"输出目录: {self.output_dir}")
        print("=" * 60)

        # 质量检查
        if not skip_checks:
            self.run_erc()
            self.run_drc()

        # 导出文件
        if not skip_exports:
            self.export_schematic_pdf()
            self.export_bom()
            self.export_gerber()
            self.export_pcb_images()

        # 生成摘要
        self.save_summary()

        print("\n" + "=" * 60)
        print("✓ 所有任务完成")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="KiCad自动化导出工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有任务
  python kicad_export.py 229_Test.kicad_pro
  
  # 只运行检查
  python kicad_export.py 229_Test.kicad_pro --skip-exports
  
  # 只导出文件
  python kicad_export.py 229_Test.kicad_pro --skip-checks
  
  # 指定输出目录
  python kicad_export.py 229_Test.kicad_pro -o build
        """,
    )

    parser.add_argument("project", help="KiCad项目文件路径 (.kicad_pro)")

    parser.add_argument(
        "-o", "--output", default="outputs", help="输出目录 (默认: outputs)"
    )

    parser.add_argument("--skip-checks", action="store_true", help="跳过ERC/DRC检查")

    parser.add_argument("--skip-exports", action="store_true", help="跳过文件导出")

    args = parser.parse_args()

    try:
        exporter = KiCadExporter(args.project, args.output)
        exporter.run_all(skip_checks=args.skip_checks, skip_exports=args.skip_exports)

        # 返回状态码
        erc_failed = exporter.results["erc"]["status"] == "failed"
        drc_failed = exporter.results["drc"]["status"] == "failed"

        if erc_failed or drc_failed:
            sys.exit(1)  # 质量检查失败
        else:
            sys.exit(0)  # 成功

    except Exception as e:
        print(f"\n✗ 错误: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
