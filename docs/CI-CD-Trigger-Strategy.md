# CI/CD 触发策略说明

## 📋 目录
- [触发时机设计](#触发时机设计)
- [执行策略](#执行策略)
- [资源优化](#资源优化)
- [实际场景示例](#实际场景示例)
- [最佳实践](#最佳实践)

---

## 触发时机设计

### ✅ 什么时候会触发构建？

#### 1. **主分支推送（自动触发）**
```yaml
触发条件：
- 分支: main 或 master
- 文件变更:
  ✓ *.kicad_pro   (项目配置)
  ✓ *.kicad_sch   (原理图)
  ✓ *.kicad_pcb   (PCB设计)
  ✓ scripts/**    (自动化脚本)
  ✓ .github/workflows/*.yml (工作流配置)

执行内容：
✓ 完整质量检查 (ERC + DRC)
✓ 导出所有文件
✓ 更新 README 状态
✓ 创建 GitHub/GitLab Release
```

**示例：**
```bash
# 这些操作会触发完整构建
git commit -m "fix: 修复原理图连接错误" 229_Test.kicad_sch
git commit -m "feat: 更新PCB布局" 229_Test.kicad_pcb

# 这些操作不会触发
git commit -m "docs: 更新README" README.md
git commit -m "chore: 添加许可证" LICENSE
```

---

#### 2. **Pull Request / Merge Request（轻量检查）**
```yaml
触发条件：
- 创建 PR/MR 到 main/master
- KiCad 文件变更

执行内容：
✓ 质量检查 (ERC + DRC)
✗ 跳过文件导出（节省时间）
✗ 不更新 README
✗ 不创建 Release

优势：
⚡ 快速反馈（约1分钟）
💰 节省 Actions 配额
📊 代码审查前发现问题
```

**示例：**
```bash
# 开发分支工作
git checkout -b feature/add-voltage-regulator
git commit -m "feat: 添加稳压电路"
git push origin feature/add-voltage-regulator

# 创建PR后自动触发检查（只检查，不导出）
```

---

#### 3. **手动触发（完全控制）**
```yaml
触发方式：
- GitHub: Actions → 选择工作流 → Run workflow
- GitLab: CI/CD → Pipelines → Run pipeline

可选参数：
□ 跳过 ERC/DRC 检查
□ 跳过文件导出
□ 是否创建 Release

使用场景：
🔧 调试工作流
📦 重新生成特定版本
🚀 手动发布里程碑版本
```

**GitHub Actions 手动触发界面：**
```
┌─────────────────────────────────────┐
│ Run workflow                        │
├─────────────────────────────────────┤
│ Branch: main                     ▼  │
│                                     │
│ ☐ 跳过 ERC/DRC 检查                 │
│ ☐ 跳过文件导出                      │
│ ☑ 创建 Release                      │
│                                     │
│         [ Run workflow ]            │
└─────────────────────────────────────┘
```

---

### ❌ 什么时候不会触发？

#### 不触发的文件变更
```yaml
✗ README.md, LICENSE, .gitignore
✗ docs/** (文档目录)
✗ docker/** (Docker配置)
✗ 图片、PDF等非源文件
✗ 备份文件 (*-backups/*)
```

#### 特殊提交标记
```bash
# 使用 [skip ci] 跳过构建
git commit -m "docs: 更新文档 [skip ci]"
git commit -m "ci: 临时禁用检查 [ci skip]"

# README自动更新使用此标记防止循环触发
```

---

## 执行策略

### 📊 三种执行模式对比

| 模式 | 触发方式 | ERC/DRC | 文件导出 | README更新 | Release | 时间 | 配额消耗 |
|------|---------|---------|---------|-----------|---------|------|---------|
| **完整构建** | 主分支推送 | ✅ | ✅ | ✅ | ✅ | 2-4分钟 | ⭐⭐⭐ |
| **PR检查** | Pull Request | ✅ | ❌ | ❌ | ❌ | 1-2分钟 | ⭐ |
| **自定义** | 手动触发 | 可选 | 可选 | 可选 | 可选 | 变化 | 变化 |

---

### 🔍 检查策略（ERC/DRC）

#### 智能错误级别区分
```python
检查结果处理：
┌─────────────────────────────────────┐
│ 错误 (error)    → ❌ 构建失败       │
│ 警告 (warning)  → ⚠️  允许通过     │
│ 排除 (exclusion)→ ✓  忽略          │
└─────────────────────────────────────┘
```

#### 检查报告输出
```bash
outputs/
├── erc_report.json      # 原始JSON报告
├── drc_report.json      # 原始JSON报告
└── build_summary.md     # 人类可读摘要
```

**报告解读示例：**
```json
{
  "violations": [
    {
      "type": "pin_not_connected",
      "severity": "error",       // ← 这个会导致构建失败
      "description": "Pin 5 未连接",
      "excluded": false
    },
    {
      "type": "different_unit_footprint",
      "severity": "warning",     // ← 这个不会导致失败
      "description": "元件封装不一致",
      "excluded": false
    },
    {
      "type": "duplicate",
      "severity": "warning",     // ← 已排除，完全忽略
      "excluded": true
    }
  ]
}
```

---

### 📦 导出策略

#### 完整导出清单
```bash
主分支推送时导出：
├── 📄 原理图PDF        (必须)
├── 📋 BOM清单         (必须)
├── 📦 Gerber文件      (必须)
├── 🖼️  PCB图像 (SVG)  (推荐)
└── 🧊 3D模型 (STEP)   (可选，可能失败)

PR检查时：
└── （不导出，只检查）
```

#### 3D模型导出说明
```yaml
状态: 可选功能
原因: 可能缺少自定义3D模型库
策略: 
  - 失败时自动清理不完整文件
  - 不影响其他导出
  - 继续构建流程
```

---

### 🏷️ Release创建策略

#### 何时创建Release？

**自动创建（主分支）：**
```yaml
条件:
  ✓ 推送到 main/master
  ✓ KiCad文件有变更
  ✓ 构建成功完成

Release内容:
  - Tag: {项目名}-build-{编号}
  - 附件: 所有导出文件
  - 描述: build_summary.md
```

**手动创建（可选）：**
```yaml
场景:
  - 重要里程碑版本
  - 发布给制造商
  - 存档历史版本

方法:
  1. Actions → Run workflow
  2. 勾选 "创建 Release"
  3. 运行
```

---

## 资源优化

### 💰 Actions 配额管理

#### GitHub Actions 免费配额
```
公开仓库: 无限制
私有仓库: 2000 分钟/月

优化策略:
✓ PR只检查不导出   → 节省 50% 时间
✓ 路径过滤触发     → 减少 70% 无效构建
✓ KiCad缓存复用    → 加速 60%（30s vs 90s）
✓ Artifacts分级保留 → PR保留7天，主分支30天
```

#### 实际消耗估算
```bash
# 优化前（每次推送都完整构建）
每日10次推送 × 4分钟 = 40分钟/天 × 30天 = 1200分钟/月

# 优化后（智能触发）
- 文档提交: 0分钟（不触发）× 5次 = 0
- PR检查: 1分钟 × 3次 = 3分钟
- 主分支构建: 3分钟 × 2次 = 6分钟
----------------------------------------
总计: 9分钟/天 × 30天 = 270分钟/月 ✅
节省: 77% 配额
```

---

### ⚡ 构建速度优化

#### 缓存策略
```yaml
缓存内容:
  - KiCad安装标记 (~/.kicad-installed)
  - Snap包缓存

加速效果:
  首次构建: 90秒 (下载+安装KiCad)
  后续构建: 30秒 (命中缓存)
  
  加速比: 3倍
```

#### 并行化（未来可能）
```yaml
可能的并行任务:
  - ERC检查    \
  - DRC检查     } 并行执行
  - PDF导出    /
  
预期加速: 20-30%
```

---

## 实际场景示例

### 场景1：日常开发迭代

**工作流程：**
```bash
# 1. 创建功能分支
git checkout -b feature/add-usb-connector

# 2. 修改设计（多次提交，不触发CI）
git commit -m "wip: 添加USB连接器"
git commit -m "wip: 更新走线"

# 3. 准备合并时创建PR
git push origin feature/add-usb-connector

# GitHub自动触发：
#   ✓ ERC/DRC检查（1分钟）
#   ✗ 不导出文件
#   结果显示在PR页面

# 4. 修复检查发现的问题
git commit -m "fix: 修复USB走线间距"
git push  # 再次触发快速检查

# 5. 审查通过后合并到main
git checkout main
git merge feature/add-usb-connector
git push  # 触发完整构建

# GitHub自动执行：
#   ✓ 完整检查
#   ✓ 导出所有文件
#   ✓ 更新README
#   ✓ 创建Release
```

**时间对比：**
```
优化前: 每次提交4分钟 × 5次 = 20分钟
优化后: 开发阶段0分钟 + PR检查1分钟×2 + 最终构建3分钟 = 5分钟
节省: 75%
```

---

### 场景2：紧急修复

**需求：** 发现关键错误，需要快速验证和发布

```bash
# 1. 直接在main分支修复（小改动）
git checkout main
git pull

# 2. 修复问题
# 编辑 229_Test.kicad_sch
git commit -m "fix: 修复电源引脚连接错误"

# 3. 推送触发自动构建
git push  # 自动触发

# GitHub执行：
#   ✓ 检查（验证修复）
#   ✓ 导出文件
#   ✓ 创建Release（立即可用）

# 4. 下载Release给制造商
# 无需手动操作，Release已自动创建
```

---

### 场景3：里程碑发布

**需求：** 为重要版本创建标记的Release

```bash
# 方法1：使用Git标签触发
git tag -a v1.0.0 -m "正式版本1.0.0"
git push origin v1.0.0

# 方法2：手动触发工作流
# GitHub Actions → Run workflow
#   Branch: main
#   ☐ 跳过检查
#   ☐ 跳过导出  
#   ☑ 创建Release
#   [ Run workflow ]

# 结果：
# Release名称: 229_Test-build-123
# 包含: 完整导出文件 + 检查报告
```

---

### 场景4：文档更新

**需求：** 只更新README，不需要重新构建

```bash
# 编辑文档
git commit -m "docs: 更新安装说明"
git push

# 结果：不触发CI（文档在paths-ignore中）
# 优势：节省时间和配额
```

---

## 最佳实践

### ✅ DO（推荐做法）

#### 1. 开发时使用分支
```bash
# ✓ 好的做法
git checkout -b feature/my-changes
# ... 多次提交开发
git push  # 创建PR时才触发检查
```

#### 2. 有意义的提交信息
```bash
# ✓ 好的提交信息（便于追踪）
git commit -m "fix: 修复U3稳压器输出短路 (关闭#15)"
git commit -m "feat: 添加USB-C供电电路"
git commit -m "docs: 更新BOM清单 [skip ci]"
```

#### 3. PR前本地验证
```bash
# 本地运行检查工具（如果可能）
python3 scripts/kicad_export.py 229_Test.kicad_pro -o outputs

# 检查报告
cat outputs/erc_report.json | jq '.violations | length'
```

#### 4. 合理使用[skip ci]
```bash
# 只更新文档时使用
git commit -m "docs: 修正错别字 [skip ci]"
git commit -m "chore: 更新.gitignore [skip ci]"
```

#### 5. 定期清理旧Artifacts
```
GitHub → Actions → 选择旧的workflow运行 → Delete
或者依赖自动过期（PR: 7天，主分支: 30天）
```

---

### ❌ DON'T（避免的做法）

#### 1. 直接在main分支频繁提交
```bash
# ✗ 不好的做法（每次都触发完整构建）
git checkout main
git commit -m "test1"
git push
git commit -m "test2"
git push
# 浪费配额和时间
```

#### 2. 提交无关文件
```bash
# ✗ 避免提交这些
git add *.bak
git add *~
git add .DS_Store

# ✓ 使用 .gitignore
echo "*.bak" >> .gitignore
echo "*~" >> .gitignore
```

#### 3. 忽略PR检查失败
```bash
# ✗ 不要强制合并失败的PR
# 即使是"只是警告"，也应该：
# 1. 检查是否真的可以忽略
# 2. 如果可以，在KiCad中排除该警告
# 3. 重新触发检查确保通过
```

#### 4. 过度依赖手动触发
```bash
# ✗ 如果经常需要手动触发，说明自动触发配置有问题
# 应该调整 paths 配置，而不是每次手动运行
```

---

## 故障排除

### 常见问题

#### Q1: 修改了KiCad文件但没有触发CI
```bash
# 检查清单：
1. 确认文件扩展名正确（.kicad_pro/.kicad_sch/.kicad_pcb）
2. 确认推送到了main/master分支
3. 确认提交信息中没有 [skip ci]
4. 检查GitHub Actions是否启用

# 查看工作流文件：
cat .github/workflows/kicad-ci.yml | grep -A 10 "paths:"
```

#### Q2: PR创建后没有运行检查
```bash
# 原因：PR没有修改KiCad文件
# 解决：如果需要强制运行，可以手动触发
# GitHub Actions → 选择工作流 → Run workflow
```

#### Q3: 构建太慢
```bash
# 检查缓存是否工作：
# Actions → 最近的运行 → 展开 "Cache KiCad" 步骤
# 应该看到 "Cache restored from key: ..."

# 如果缓存未命中，尝试：
1. 清理旧缓存（Settings → Actions → Caches）
2. 重新运行工作流
```

#### Q4: README状态未更新
```bash
# 检查：
1. 确认 build_status.md 是否生成
2. 确认工作流有写权限（Settings → Actions → Workflow permissions）
3. 查看 "Update README" 步骤的日志

# 手动更新：
python3 scripts/update_readme.py -o outputs -r README.md -b 123
```

---

## 配置调整指南

### 修改触发文件模式

**添加更多KiCad文件类型：**
```yaml
# .github/workflows/kicad-ci.yml
on:
  push:
    paths:
      - '**.kicad_pro'
      - '**.kicad_sch'
      - '**.kicad_pcb'
      - '**.kicad_wks'   # 添加：工作表模板
      - 'sym-lib-table'  # 添加：符号库表
      - 'fp-lib-table'   # 添加：封装库表
```

---

### 调整Artifacts保留期

**根据存储需求调整：**
```yaml
# GitHub Actions
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    retention-days: ${{ github.event_name == 'pull_request' && 3 || 60 }}
    #                                              PR: 3天 ↑    主分支: 60天 ↑
```

---

### 禁用某些导出

**如果不需要某些文件：**
```python
# scripts/kicad_export.py
# 注释掉不需要的导出：
# run_export_svg(args.project, args.output)  # 禁用SVG导出
# run_export_step(args.project, args.output) # 禁用STEP导出
```

---

## 总结

### 核心原则
1. **按需触发** - 只在必要时运行完整构建
2. **分级检查** - PR快速检查，主分支完整验证
3. **资源节约** - 合理使用缓存和路径过滤
4. **快速反馈** - 1-2分钟内发现问题
5. **自动发布** - 减少手动操作

### 典型工作流总结
```
开发分支 (不触发)
    ↓
    ├─ 多次本地提交
    ↓
创建PR (快速检查: 1分钟)
    ↓
    ├─ ERC/DRC ✓
    ├─ 跳过导出
    ↓
合并到main (完整构建: 3分钟)
    ↓
    ├─ 完整检查 ✓
    ├─ 导出所有文件 ✓
    ├─ 更新README ✓
    └─ 创建Release ✓
```

### 效果对比
| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 单次构建时间 | 4分钟 | 1-3分钟 | -25% |
| 月度配额消耗 | 1200分钟 | 270分钟 | -77% |
| 开发反馈速度 | 每次4分钟 | PR时1分钟 | +75% |
| 无效触发次数 | 高（文档也触发） | 低（只KiCad文件） | -70% |

---

**相关文档：**
- [工具使用说明](../scripts/README.md)
- [README自动更新](./README-Auto-Update.md)
- [GitHub vs GitLab对比](./CI-CD-Comparison.md)
- [完整系统概述](./SUMMARY.md)
