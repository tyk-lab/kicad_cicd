# 229测试板 KiCad项目

[![KiCad CI/CD](https://github.com/tyk-lab/kicad_cicd/actions/workflows/kicad-ci.yml/badge.svg)](https://github.com/tyk-lab/kicad_cicd/actions/workflows/kicad-ci.yml)

这是一个使用KiCad设计的PCB项目，包含自动化CI/CD流程。

<!-- BUILD_STATUS_START -->
## 📊 最新构建状态

**构建 #24** | **状态: ✗ 失败** | **时间: 2025-11-03 06:55:20 UTC**

![ERC](https://img.shields.io/badge/ERC-✓_通过-success) ![DRC](https://img.shields.io/badge/DRC-✗_12_错误-critical)

<details>
<summary>📋 详细报告</summary>

### ERC 检查
- **状态**: PASSED
- **错误**: 0 个
- **警告**: 0 个

### DRC 检查
- **状态**: FAILED
- **错误**: 12 个
- **警告**: 18 个

</details>

<!-- BUILD_STATUS_END -->

## 项目概述

- **项目名称**: 229测试板
- **KiCad版本**: 7.0+
- **PCB层数**: 2层

## 自动化构建

每次推送到主分支时，GitHub Actions会自动执行以下操作：

- ✅ **ERC检查** - 电气规则检查
- ✅ **DRC检查** - 设计规则检查
- ✅ **原理图导出** - 生成PDF文档
- ✅ **BOM导出** - 元件清单
- ✅ **Gerber生成** - 制造文件
- ✅ **PCB图像** - 可视化预览

## 最新构建输出

### PCB预览

![PCB正面](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-PCB-Front.svg)

### 下载文件

访问 [Releases页面](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest) 下载最新的构建输出：

- 📄 [原理图PDF](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-Schematic.pdf)
- 📋 [BOM清单](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-BOM.csv)
- 📦 [Gerber文件](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-Gerber.zip)
- 🖼️ [PCB正面图](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-PCB-Front.svg)
- 🖼️ [PCB背面图](https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/229_Test-PCB-Back.svg)

## 项目结构

```
.
├── 229_Test.kicad_pro      # KiCad项目文件
├── 229_Test.kicad_sch      # 原理图文件
├── 229_Test.kicad_pcb      # PCB文件
├── GERBER/                 # Gerber输出目录
└── .github/
    └── workflows/
        └── kicad-ci.yml    # CI/CD配置
```

## 本地开发

### 前置要求

- KiCad 7.0或更高版本
- Git

### 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 打开项目

使用KiCad打开 `229_Test.kicad_pro` 文件。

## 手动触发构建

1. 访问项目的 [Actions页面](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
2. 选择 "KiCad CI/CD" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

## 检查报告

每次构建都会生成ERC和DRC检查报告，可以在以下位置查看：

- ERC报告: `erc_report.json`
- DRC报告: `drc_report.json`

这些报告也会作为artifacts上传到GitHub Actions，并包含在Release中。

## 许可证

请在此添加您的许可证信息。

## 贡献

欢迎提交Issue和Pull Request！

---

*此README由GitHub Actions自动更新*
