# CI/CD 配置文件审核与修复

## 📋 审核时间
2025-11-03

## 🔍 发现的问题

### GitHub Actions (.github/workflows/kicad-ci.yml)

#### ❌ 问题 1: 缓存Key引用错误 (Line 78)
**错误代码:**
```yaml
key: kicad-snap-${{ runner.os }}-${{ hashFiles('.github/workflows/kicad-ci-simple.yml') }}
```

**问题:** 文件名不存在，应该是 `kicad-ci.yml` 而不是 `kicad-ci-simple.yml`

**修复:**
```yaml
key: kicad-snap-${{ runner.os }}-${{ hashFiles('.github/workflows/kicad-ci.yml') }}
```

---

#### ❌ 问题 2-4: workflow_dispatch inputs 访问方式错误 (Line 148-153, 210, 224)

**错误代码:**
```yaml
if [ "${{ inputs.skip_checks }}" = "true" ]; then
if [ "${{ inputs.skip_exports }}" = "true" ]; then

if: (github.event_name == 'workflow_dispatch' && inputs.create_release == true)
```

**问题:** 
- 在 GitHub Actions 中，`workflow_dispatch` 的 inputs 需要通过 `github.event.inputs` 访问
- 布尔值比较需要用字符串 `'true'` 而不是布尔 `true`

**修复:**
```yaml
if [ "${{ github.event.inputs.skip_checks }}" = "true" ]; then
if [ "${{ github.event.inputs.skip_exports }}" = "true" ]; then

if: (github.event_name == 'workflow_dispatch' && github.event.inputs.create_release == 'true')
```

**参考文档:**
- [GitHub Actions - workflow_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)

---

### GitLab CI (.gitlab-ci.yml)

#### ❌ 问题 5: artifacts 在 rules 中嵌套定义 (Line 180-189)

**错误代码:**
```yaml
artifacts:
  name: "..."
  paths: [...]
  expire_in: 7 days
  
rules:
  - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    artifacts:
      expire_in: 7 days  # ❌ 不允许在rules中重新定义artifacts
```

**问题:** GitLab CI 不支持在 `rules` 中重新定义 `artifacts` 属性

**修复:**
```yaml
artifacts:
  name: "${KICAD_PROJECT_NAME}-outputs-$CI_PIPELINE_ID"
  paths:
    - ${OUTPUT_DIR}/
  expire_in: 30 days  # 统一使用30天
  when: always
```

**替代方案（如果需要条件性保留期）:**
在 workflow level 的 rules 中使用变量控制，或者创建不同的 jobs

**参考文档:**
- [GitLab CI - artifacts](https://docs.gitlab.com/ee/ci/yaml/#artifacts)
- [GitLab CI - rules](https://docs.gitlab.com/ee/ci/yaml/#rules)

---

#### ❌ 问题 6: only 和 rules 混用 (Line 282)

**错误代码:**
```yaml
create-release:
  rules:
    - if: '...'
      when: always
  
  only:      # ❌ 与 rules 冲突
    - main
    - master
    - tags
```

**问题:** GitLab CI 中 `only/except` 和 `rules` 不能同时使用，会导致配置错误

**修复:**
```yaml
create-release:
  rules:
    - if: '($CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master") && $SKIP_RELEASE != "true"'
      when: always
    - when: never
  # 移除 only 配置
```

**参考文档:**
- [GitLab CI - Differences between rules and only/except](https://docs.gitlab.com/ee/ci/yaml/#differences-between-rules-and-onlyexcept)

---

## ✅ 已修复的文件

### GitHub Actions
- ✅ 缓存key文件名修正
- ✅ workflow_dispatch inputs 访问方式修正（3处）
- ✅ 布尔值比较方式修正

### GitLab CI
- ✅ 移除 artifacts 在 rules 中的嵌套定义
- ✅ 移除与 rules 冲突的 only 配置
- ✅ 统一 artifacts 保留期为 30 天

---

## 🧪 需要验证的功能

### Python脚本参数支持
✅ **已确认:** `scripts/kicad_export.py` 支持以下参数：
- `--skip-checks` - 跳过 ERC/DRC 检查
- `--skip-exports` - 跳过文件导出

### 测试清单

#### GitHub Actions
- [ ] 主分支推送 - 完整构建
- [ ] Pull Request - 只检查不导出
- [ ] 手动触发 - 带自定义选项
  - [ ] 跳过检查
  - [ ] 跳过导出
  - [ ] 不创建Release
- [ ] 文档修改 - 不触发构建
- [ ] KiCad缓存 - 第二次运行应该更快

#### GitLab CI
- [ ] 主分支推送 - 完整构建
- [ ] Merge Request - 只检查不导出
- [ ] 手动触发 - 完整控制
- [ ] 文档修改 - 不触发构建
- [ ] Artifacts 保留期正确

---

## 📊 配置对比

### 触发策略对比

| 触发方式 | GitHub Actions | GitLab CI | 执行内容 |
|---------|---------------|-----------|---------|
| 主分支推送 | `push` + `paths` | `workflow.rules` + `changes` | 完整构建 |
| PR/MR | `pull_request` + `paths` | `merge_request_event` + `changes` | 只检查 |
| 手动触发 | `workflow_dispatch` + `inputs` | `web` | 自定义 |

### 条件执行对比

| 步骤 | GitHub | GitLab |
|------|--------|--------|
| 更新README | `if: github.event_name == 'push'` | `rules: - if: $CI_COMMIT_BRANCH` |
| 创建Release | `if: ... && github.event.inputs.create_release` | `rules: - if: ... && $SKIP_RELEASE` |

---

## 🔧 建议的改进

### 1. 环境变量统一
考虑在两个平台使用相同的变量名：
- `KICAD_PROJECT_NAME`
- `OUTPUT_DIR`
- `SKIP_CHECKS`
- `SKIP_EXPORTS`
- `CREATE_RELEASE`

### 2. 错误处理增强
```yaml
# 添加更详细的错误信息
- name: Run checks
  run: |
    if ! python3 scripts/kicad_export.py ...; then
      echo "::error::KiCad导出失败，检查 ${OUTPUT_DIR}/build_summary.md"
      exit 1
    fi
```

### 3. 通知集成（可选）
- GitHub: 使用 Actions 通知到 Slack/Discord
- GitLab: 使用 CI/CD 通知到聊天工具

### 4. 性能监控
```yaml
# 添加性能统计
- name: Build Statistics
  run: |
    echo "构建时长: ${{ job.duration }}"
    echo "缓存命中: ${{ steps.cache-kicad.outputs.cache-hit }}"
```

---

## 📚 相关文档

- [GitHub Actions 语法](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitLab CI/CD 语法](https://docs.gitlab.com/ee/ci/yaml/)
- [CI/CD触发策略详解](./CI-CD-Trigger-Strategy.md)
- [GitHub vs GitLab对比](./CI-CD-Comparison.md)

---

## 🎯 总结

### 修复前的问题
- ❌ 5个语法错误
- ❌ 1个逻辑冲突
- ⚠️ 潜在的运行时错误

### 修复后的状态
- ✅ 所有语法错误已修复
- ✅ 配置逻辑正确
- ✅ 符合平台最佳实践
- ✅ 准备好进行测试

### 下一步
1. 提交修复到版本控制
2. 在实际环境中测试
3. 根据测试结果进行微调
4. 更新文档反映实际行为
