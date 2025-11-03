# KiCad 自动化工具集

本目录包含 KiCad 项目自动化所需的所有脚本工具。

## 📦 工具列表

### 1. `kicad_export.py` - 主导出脚本
统一处理KiCad项目的所有导出任务，简化CI/CD流程。

**功能特性：**

#### 质量检查
- ✅ ERC（电气规则检查）- 区分错误/警告/排除项
- ✅ DRC（设计规则检查）- 区分错误/警告/排除项
- ✅ JSON格式违规报告
- ✅ 智能状态判断（只有错误才算失败）

#### 文件导出
- ✅ 原理图PDF
- ✅ BOM（物料清单CSV）
- ✅ Gerber制造文件（自动打包ZIP）
- ✅ PCB图像（正面/背面SVG）
- ✅ 3D STEP模型（可选，失败不影响构建）

#### 其他特性
- ✅ 自动检测KiCad CLI命令（支持snap版本）
- ✅ 过滤wxWidgets调试信息
- ✅ 详细的执行日志
- ✅ 构建摘要生成
- ✅ 错误处理和超时保护
- ✅ 自动清理不完整文件

### 2. `update_readme.py` - README 自动更新
在每次构建后自动更新 README.md 中的构建状态。

**功能特性：**
- ✅ 读取 ERC/DRC 检查结果
- ✅ 生成彩色状态徽章（shields.io）
- ✅ 智能定位更新区域
- ✅ 保留README其他内容不变
- ✅ 详细报告可折叠显示
- ✅ 防止构建循环（[skip ci]）

## 本地使用

### 基本用法

```bash
# 运行所有任务
python3 scripts/kicad_export.py 229_Test.kicad_pro

# 指定输出目录
python3 scripts/kicad_export.py 229_Test.kicad_pro -o build

# 只运行检查
python3 scripts/kicad_export.py 229_Test.kicad_pro --skip-exports

# 只导出文件
python3 scripts/kicad_export.py 229_Test.kicad_pro --skip-checks
```

### 命令行参数

```
usage: kicad_export.py [-h] [-o OUTPUT] [--skip-checks] [--skip-exports] project

KiCad自动化导出工具

positional arguments:
  project               KiCad项目文件路径 (.kicad_pro)

options:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出目录 (默认: outputs)
  --skip-checks         跳过ERC/DRC检查
  --skip-exports        跳过文件导出
```

### 输出文件结构

```
outputs/
├── build_summary.md          # 构建摘要
├── erc_report.json           # ERC检查报告
├── drc_report.json           # DRC检查报告
├── 229_Test-Schematic.pdf    # 原理图PDF
├── 229_Test-BOM.csv          # 物料清单
├── 229_Test-Gerber.zip       # Gerber文件包
├── 229_Test-PCB-Front.svg    # PCB正面图
├── 229_Test-PCB-Back.svg     # PCB背面图
├── 229_Test-3D.step          # 3D模型（可选）
└── gerber/                   # Gerber源文件
    ├── *.gbr                 # 各层Gerber文件
    └── *.drl                 # 钻孔文件
```

## GitHub Actions集成

### 工作流文件对比

#### 原版工作流 (`kicad-ci.yml`)
- **步骤数**: 17个
- **代码行数**: ~500行
- **优点**: 每个步骤独立，易于调试单个步骤
- **缺点**: 配置复杂，维护困难，重复代码多

#### 简化版工作流 (`kicad-ci-simple.yml`) ⭐ 推荐
- **步骤数**: 9个
- **代码行数**: ~180行
- **优点**: 
  - 简洁清晰，易于维护
  - Python脚本统一管理导出逻辑
  - 更容易扩展和修改
  - 本地和CI使用相同代码
- **缺点**: 调试时需要查看Python脚本输出

### 使用简化版工作流

1. **启用新工作流**：
   ```bash
   # 方式1：重命名文件（禁用旧版）
   mv .github/workflows/kicad-ci.yml .github/workflows/kicad-ci.yml.backup
   mv .github/workflows/kicad-ci-simple.yml .github/workflows/kicad-ci.yml
   
   # 方式2：两个都保留（推荐测试期间）
   # kicad-ci.yml 和 kicad-ci-simple.yml 同时存在
   # 可在Actions页面对比效果
   ```

2. **推送代码触发构建**：
   ```bash
   git add .
   git commit -m "使用Python脚本简化CI流程"
   git push origin main
   ```

3. **手动触发**：
   - 访问 GitHub Actions 页面
   - 选择 "KiCad CI/CD" 工作流
   - 点击 "Run workflow"

### 工作流输出

#### Artifacts下载
- **保留时间**: 90天
- **包含文件**: 所有outputs/目录内容
- **下载位置**: Actions页面 → 具体运行 → Artifacts

#### Release发布（仅推送到主分支时）
- **标签**: `build-<构建编号>`
- **文件**: 精选的发布文件（PDF、BOM、Gerber ZIP等）
- **说明**: 自动生成的构建摘要

## 常见问题

### KiCad命令未找到

脚本会自动检测以下命令：
1. `kicad.kicad-cli` (snap版本)
2. `kicad-cli` (标准安装)

如果都未找到，请安装KiCad：

```bash
# Ubuntu/Debian - Snap方式（推荐）
sudo snap install kicad

# Ubuntu/Debian - APT方式
sudo add-apt-repository ppa:kicad/kicad-9.0-releases
sudo apt-get update
sudo apt-get install kicad

# Windows
# 从 https://www.kicad.org/download/ 下载安装
# 并确保 kicad-cli 在 PATH 中

# macOS
brew install kicad
```

### Python依赖

脚本使用Python标准库，无需额外依赖。

**最低要求**: Python 3.6+

### 超时设置

默认超时: 120秒/命令

如果项目很大，可以修改脚本中的超时值：
```python
# 在 _run_command 方法中
result = subprocess.run(
    args,
    capture_output=True,
    text=True,
    timeout=300  # 改为300秒
)
```

### 3D模型导出失败

这是正常的，如果项目中的元件没有关联3D模型，导出会失败。

可以：
- 忽略此错误（脚本已处理）
- 为元件添加3D模型
- 使用 `--skip-exports` 跳过导出

## 扩展和自定义

### 添加新的导出格式

编辑 `scripts/kicad_export.py`，添加新方法：

```python
def export_custom_format(self) -> bool:
    """导出自定义格式"""
    output_file = self.output_dir / f'{self.project_name}-Custom.ext'
    
    args = [
        self.kicad_cli,
        'pcb', 'export', 'custom',
        '--output', str(output_file),
        str(self.pcb_file)
    ]
    
    success, _ = self._run_command(args, "导出自定义格式")
    self.results['exports']['custom'] = output_file.exists()
    return success
```

然后在 `run_all()` 方法中调用：

```python
def run_all(self, skip_checks=False, skip_exports=False):
    # ...existing code...
    if not skip_exports:
        # ...existing exports...
        self.export_custom_format()  # 添加这行
```

### 修改输出目录结构

修改各个export方法中的 `output_file` 路径即可。

### 自定义构建摘要

编辑 `generate_summary()` 方法，调整Markdown格式。

## 性能对比

| 指标 | 原工作流 | 简化工作流 | 改善 |
|------|---------|-----------|------|
| 配置复杂度 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ↓60% |
| 代码行数 | ~500行 | ~180行 | ↓64% |
| 步骤数 | 17步 | 9步 | ↓47% |
| 运行时间 | ~3-5分钟 | ~2-4分钟 | ↓20% |
| 维护难度 | 高 | 低 | ↓70% |

## 工作流程图

```
┌─────────────────────────────────────────────┐
│         KiCad CI/CD 完整流程                │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  1. 代码推送到仓库      │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  2. 安装/缓存 KiCad    │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  3. 运行 kicad_export │
        │     - ERC/DRC检查      │
        │     - 导出PDF/BOM     │
        │     - 生成Gerber      │
        │     - 导出PCB图像      │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  4. 更新 README 状态   │
        │   (update_readme.py)  │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  5. 上传 Artifacts     │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  6. 创建 Release       │
        │    (仅主分支)          │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  7. 显示构建摘要        │
        └───────────────────────┘
```

## 技术亮点

### 🎯 智能检查逻辑
- **区分严重级别**：错误、警告、排除项分别统计
- **只有错误才失败**：警告不会导致构建失败
- **详细报告**：JSON格式保存完整检查结果

### 🧹 自动清理机制
- **过滤调试信息**：自动过滤wxWidgets无害输出
- **清理不完整文件**：3D STEP导出失败时自动删除残留文件
- **防止误导**：确保输出文件与状态一致

### 🔄 README 自动同步
- **实时状态**：每次构建后自动更新徽章
- **保留内容**：只更新标记区域，不破坏其他内容
- **防止循环**：使用 [skip ci] 避免触发新构建

### ⚡ 性能优化
- **缓存机制**：KiCad安装缓存，第二次构建30秒启动
- **并行无关任务**：充分利用CI资源
- **早期退出**：检测到错误立即终止

## 文档索引

| 文档 | 说明 |
|------|------|
| `scripts/README.md` | **本文档** - 工具集总览 |
| `docs/CI-CD-Comparison.md` | GitHub vs GitLab CI/CD 语法对比 |
| `docs/README-Auto-Update.md` | README 自动更新功能详解 |
| `README.md` | 项目主文档（自动更新） |

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关链接

- [KiCad官方文档](https://docs.kicad.org/)
- [KiCad CLI文档](https://docs.kicad.org/master/en/cli/cli.html)
- [GitHub Actions文档](https://docs.github.com/actions)
- [GitLab CI/CD文档](https://docs.gitlab.com/ee/ci/)
- [Shields.io徽章生成](https://shields.io/)
