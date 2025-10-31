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
    def __init__(self, project_path: str, output_dir: str = "outputs"):
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

            if result.returncode == 0:
                print(f"✓ {description} - 成功")
                return True, result.stdout
            else:
                print(f"⚠ {description} - 失败 (退出码: {result.returncode})")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            print(f"⚠ {description} - 超时")
            return False, "命令执行超时"
        except Exception as e:
            print(f"⚠ {description} - 异常: {str(e)}")
            return False, str(e)

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
            "--exit-code-violations",
            "--severity-all",
            "--format",
            "json",
            "--output",
            str(report_file),
            str(self.sch_file),
        ]

        success, output = self._run_command(args, "ERC检查")

        # 解析结果
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    violations = len(data.get("violations", []))

                    self.results["erc"] = {
                        "status": "passed" if violations == 0 else "failed",
                        "violations": violations,
                    }

                    if violations > 0:
                        print(f"  发现 {violations} 个违规项")
                    else:
                        print("  未发现违规项")

            except json.JSONDecodeError:
                self.results["erc"] = {"status": "error", "violations": "unknown"}

        return success

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
            "--exit-code-violations",
            "--severity-all",
            "--format",
            "json",
            "--output",
            str(report_file),
            str(self.pcb_file),
        ]

        success, output = self._run_command(args, "DRC检查")

        # 解析结果
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    violations = len(data.get("violations", []))

                    self.results["drc"] = {
                        "status": "passed" if violations == 0 else "failed",
                        "violations": violations,
                    }

                    if violations > 0:
                        print(f"  发现 {violations} 个违规项")
                    else:
                        print("  未发现违规项")

            except json.JSONDecodeError:
                self.results["drc"] = {"status": "error", "violations": "unknown"}

        return success

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

        # 导出3D STEP模型（可选）
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

        success, _ = self._run_command(args_step, "导出3D STEP模型")
        self.results["exports"]["step_3d"] = step_file.exists()

        if not step_file.exists():
            print("  ℹ 3D模型导出失败（可能缺少3D模型库）")

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
            ("schematic_pdf", "Schematic PDF"),
            ("bom", "BOM (Bill of Materials)"),
            ("gerber_zip", "Gerber files (ZIP)"),
            ("pcb_front_svg", "PCB Front Image (SVG)"),
            ("pcb_back_svg", "PCB Back Image (SVG)"),
            ("step_3d", "3D STEP Model"),
        ]

        for key, name in exports:
            status = "✓" if self.results["exports"].get(key, False) else "✗"
            summary += f"- {status} {name}\n"

        return summary

    def _format_check_status(self, check_type: str) -> str:
        """格式化检查状态"""
        result = self.results[check_type]
        status = result["status"]
        violations = result["violations"]

        if status == "passed":
            return "✓ 通过"
        elif status == "failed":
            return f"⚠ 失败 ({violations} 个违规项)"
        elif status == "error":
            return "✗ 错误"
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
