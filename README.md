# 229测试板 KiCad项目

[![KiCad CI/CD](https://github.com/tyk-lab/kicad_cicd/actions/workflows/kicad-ci.yml/badge.svg)](https://github.com/tyk-lab/kicad_cicd/actions/workflows/kicad-ci.yml)

这是一个使用KiCad设计的PCB项目，包含自动化CI/CD流程。

<!-- BUILD_STATUS_START -->
## 📊 最新构建状态

**构建 #0** | **状态: 等待首次构建** | **时间: --**

![ERC](https://img.shields.io/badge/ERC-待运行-lightgrey) ![DRC](https://img.shields.io/badge/DRC-待运行-lightgrey)

<!-- BUILD_STATUS_END -->

## 项目概述

- **项目名称**: 229测试板
- **KiCad版本**: 7.0+
- **PCB层数**: 2层

## 🚀 自动化构建

每次推送到主分支时，CI/CD 会自动执行以下操作：

### 质量检查
- ✅ **ERC检查** - 电气规则检查（区分错误/警告）
- ✅ **DRC检查** - 设计规则检查（区分错误/警告）
- ✅ **智能判断** - 只有错误才会导致构建失败

### 文件导出
- ✅ **原理图PDF** - 完整电路图文档
- ✅ **BOM清单** - CSV格式物料清单
- ✅ **Gerber文件** - 生产制造文件包
- ✅ **PCB图像** - SVG格式正反面预览
- ✅ **3D模型** - STEP格式（可选）

### 自动发布
- 📦 **构建产物** - 自动上传到 Artifacts
- 🏷️ **版本发布** - 自动创建 GitHub Release
- 📊 **状态同步** - 自动更新 README 徽章

## 🔧 技术特点

- **快速启动** - KiCad 缓存机制，30秒启动
- **智能检查** - 区分错误和警告，精准判断构建状态
- **自动清理** - 失败文件自动删除，避免误导
- **实时状态** - README 徽章实时显示构建结果
- **双平台支持** - GitHub Actions + GitLab CI/CD

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

## 📋 检查报告

每次构建都会生成详细的检查报告：

### 报告文件
- 📄 **ERC报告**: `outputs/erc_report.json` - 电气规则检查详情
- 📄 **DRC报告**: `outputs/drc_report.json` - 设计规则检查详情
- 📄 **构建摘要**: `outputs/build_summary.md` - 完整构建报告

### 查看方式
1. **Artifacts** - GitHub Actions 页面下载完整输出
2. **Release** - 每次发布包含所有报告文件
3. **README** - 顶部徽章显示实时状态

### 状态说明
- 🟢 **通过** - 无错误无警告
- 🟡 **警告** - 有警告但无错误（构建成功）
- 🔴 **失败** - 有错误（构建失败）

## 🛠️ 本地使用工具

### 快速开始
```bash
# 运行完整导出
python3 scripts/kicad_export.py 229_Test.kicad_pro

# 只运行检查
python3 scripts/kicad_export.py 229_Test.kicad_pro --skip-exports

# 指定输出目录
python3 scripts/kicad_export.py 229_Test.kicad_pro -o build
```

### 更多选项
查看 `scripts/README.md` 了解完整功能和用法。

## 📚 文档

- 📖 [工具使用指南](scripts/README.md) - Python脚本详细说明
- ⚡ [CI/CD触发策略](docs/CI-CD-Trigger-Strategy.md) - 触发时机和执行策略详解 ⭐
- 🔀 [CI/CD平台对比](docs/CI-CD-Comparison.md) - GitHub vs GitLab
- 🔄 [README自动更新](docs/README-Auto-Update.md) - 状态徽章配置
- 📋 [完整系统概述](docs/SUMMARY.md) - 系统架构和技术实现

## 许可证

请在此添加您的许可证信息。

## 贡献

欢迎提交Issue和Pull Request！

---

*此README由GitHub Actions自动更新*
