# README 自动更新功能说明

## 功能概述

CI/CD 流程会在每次构建后自动更新 README.md 中的构建状态，展示最新的 ERC/DRC 检查结果。

## 特点

✅ **自动更新** - 每次构建自动刷新状态  
✅ **保留内容** - 只更新标记区域，不破坏其他内容  
✅ **状态徽章** - 使用 shields.io 生成美观的徽章  
✅ **详细报告** - 可折叠的详细检查结果  
✅ **防止循环** - 使用 `[skip ci]` 避免触发新构建

## README 中的显示效果

### 1. 构建成功（无问题）
```markdown
## 📊 最新构建状态

**构建 #123** | **状态: ✓ 成功** | **时间: 2025-01-15 10:30:00 UTC**

![ERC](https://img.shields.io/badge/ERC-✓_通过-success) 
![DRC](https://img.shields.io/badge/DRC-✓_通过-success)
```

### 2. 构建有警告
```markdown
## 📊 最新构建状态

**构建 #124** | **状态: ⚠ 警告** | **时间: 2025-01-15 11:00:00 UTC**

![ERC](https://img.shields.io/badge/ERC-✓_通过-success) 
![DRC](https://img.shields.io/badge/DRC-⚠_5_警告-yellow)
```

### 3. 构建失败
```markdown
## 📊 最新构建状态

**构建 #125** | **状态: ✗ 失败** | **时间: 2025-01-15 12:00:00 UTC**

![ERC](https://img.shields.io/badge/ERC-✗_3_错误-critical) 
![DRC](https://img.shields.io/badge/DRC-✗_8_错误-critical)
```

## 工作原理

### 1. 标记区域

README 中使用特殊注释标记需要更新的区域：

```markdown
<!-- BUILD_STATUS_START -->
... 这里的内容会被自动替换 ...
<!-- BUILD_STATUS_END -->
```

### 2. 更新流程

```
构建完成
    ↓
读取 ERC/DRC 报告 (JSON)
    ↓
生成状态徽章和详细信息
    ↓
查找 README 标记区域
    ↓
替换标记区域内容
    ↓
提交更新 (带 [skip ci] 标签)
```

### 3. 脚本参数

```bash
python3 scripts/update_readme.py \
  -o outputs \              # 构建输出目录
  -r README.md \            # README 文件路径
  -b 123                    # 构建编号
```

## GitHub Actions 配置

在 `.github/workflows/kicad-ci.yml` 中添加：

```yaml
- name: Update README with build status
  run: |
    python3 scripts/update_readme.py \
      -o ${{ env.OUTPUT_DIR }} \
      -r README.md \
      -b ${{ github.run_number }}
    
    if git diff --quiet README.md; then
      echo "README 无变化"
    else
      git config user.name "github-actions[bot]"
      git config user.email "github-actions[bot]@users.noreply.github.com"
      git add README.md
      git commit -m "docs: 更新构建状态 #${{ github.run_number }} [skip ci]"
      git push
    fi
```

## GitLab CI/CD 配置

在 `.gitlab-ci.yml` 中添加：

```yaml
update-readme:
  stage: package
  script:
    - python3 scripts/update_readme.py -o ${OUTPUT_DIR} -r README.md -b ${CI_PIPELINE_ID}
    - |
      git config user.name "GitLab CI"
      git config user.email "ci@gitlab.com"
      if ! git diff --quiet README.md; then
        git add README.md
        git commit -m "docs: 更新构建状态 #${CI_PIPELINE_ID} [skip ci]"
        git push https://oauth2:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git HEAD:${CI_COMMIT_REF_NAME}
      fi
```

## 徽章颜色规则

| 状态 | 颜色 | 条件 |
|------|------|------|
| ✓ 通过 | 绿色 (success) | 无错误无警告 |
| ⚠ 警告 | 黄色 (yellow) | 有警告但无错误 |
| ✗ 失败 | 红色 (critical) | 有错误 |
| 未知 | 灰色 (lightgrey) | 未运行或无数据 |

## 防止构建循环

**重要**: 提交消息必须包含 `[skip ci]` 或 `[ci skip]` 标签：

```bash
git commit -m "docs: 更新构建状态 #123 [skip ci]"
```

这样可以防止 README 更新触发新的 CI 构建。

## 手动测试

本地测试 README 更新脚本：

```bash
# 假设已有构建输出
python3 scripts/update_readme.py -o outputs -r README.md -b 999

# 查看 git diff
git diff README.md
```

## 自定义

### 修改徽章样式

编辑 `scripts/update_readme.py` 中的 `generate_status_badge` 函数：

```python
def generate_status_badge(label: str, status: str, errors: int, warnings: int) -> str:
    if status == "passed":
        # 修改这里的徽章URL
        return f"![{label}](https://img.shields.io/badge/{label}-✓_通过-success?style=flat-square)"
```

### 修改显示格式

编辑 `update_readme.py` 中的 `new_status_section` 变量：

```python
new_status_section = f"""<!-- BUILD_STATUS_START -->
## 你的自定义标题

自定义内容...

<!-- BUILD_STATUS_END -->"""
```

## 故障排查

### 1. README 没有更新

**检查**:
- 确认 `scripts/update_readme.py` 有执行权限
- 查看 CI 日志中的 "Update README" 步骤输出
- 确认 README 中有 `<!-- BUILD_STATUS_START -->` 和 `<!-- BUILD_STATUS_END -->` 标记

### 2. 提交失败

**检查**:
- GitHub: 确认工作流有 `contents: write` 权限
- GitLab: 确认 CI/CD 设置中启用了 "Allow commits from CI/CD jobs"

### 3. 触发构建循环

**检查**:
- 提交消息必须包含 `[skip ci]`
- GitHub Actions: 检查触发条件是否排除了 bot 提交

## 最佳实践

1. **首次使用**: 手动添加标记到 README
2. **权限配置**: 确保 CI 有推送权限
3. **分支保护**: 允许 CI bot 推送到受保护分支
4. **提交消息**: 始终使用 `[skip ci]` 避免循环

## 示例效果

查看本项目的 README.md 顶部，可以看到实时更新的构建状态！

---

*更多信息请参考 `scripts/update_readme.py` 源代码*
