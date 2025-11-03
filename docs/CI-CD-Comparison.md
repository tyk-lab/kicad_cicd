# GitHub Actions vs GitLab CI/CD 对比说明

## 配置文件位置

| 平台 | 配置文件 | 位置 |
|------|---------|------|
| **GitHub** | `kicad-ci.yml` | `.github/workflows/kicad-ci.yml` |
| **GitLab** | `.gitlab-ci.yml` | 项目根目录 `.gitlab-ci.yml` |

## 主要语法差异

### 1. 全局变量

**GitHub Actions:**
```yaml
env:
  KICAD_PROJECT_NAME: "229_Test"
  OUTPUT_DIR: "outputs"
```

**GitLab CI/CD:**
```yaml
variables:
  KICAD_PROJECT_NAME: "229_Test"
  OUTPUT_DIR: "outputs"
```

### 2. 流水线结构

**GitHub Actions:**
```yaml
jobs:
  kicad-build:
    runs-on: ubuntu-22.04
    steps:
      - name: Step 1
        run: echo "hello"
```

**GitLab CI/CD:**
```yaml
stages:
  - setup
  - build

install-kicad:
  stage: setup
  script:
    - echo "hello"
```

### 3. 变量引用

**GitHub Actions:**
```yaml
${{ env.KICAD_PROJECT_NAME }}      # 环境变量
${{ github.run_number }}           # 内置变量
${{ secrets.GITHUB_TOKEN }}        # 密钥
```

**GitLab CI/CD:**
```yaml
${KICAD_PROJECT_NAME}              # 环境变量
${CI_PIPELINE_ID}                  # 内置变量
${CI_JOB_TOKEN}                    # 密钥（自动注入）
```

### 4. 条件执行

**GitHub Actions:**
```yaml
- name: Create Release
  if: github.ref == 'refs/heads/main'
```

**GitLab CI/CD:**
```yaml
create-release:
  only:
    - main
    - master
```

### 5. 产物（Artifacts）

**GitHub Actions:**
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: kicad-outputs
    path: outputs/
```

**GitLab CI/CD:**
```yaml
artifacts:
  name: "kicad-outputs-$CI_PIPELINE_ID"
  paths:
    - outputs/
  expire_in: 30 days
```

### 6. 缓存（Cache）

**GitHub Actions:**
```yaml
- name: Cache
  uses: actions/cache@v4
  with:
    path: ~/.kicad-installed
    key: kicad-${{ runner.os }}
```

**GitLab CI/CD:**
```yaml
cache:
  key: kicad-installation
  paths:
    - .kicad-cache/
  policy: push  # push / pull / pull-push
```

### 7. 镜像（Docker Image）

**GitHub Actions:**
```yaml
runs-on: ubuntu-22.04
```

**GitLab CI/CD:**
```yaml
image: ubuntu:22.04  # 可以使用任何 Docker 镜像
```

### 8. 内置变量对比

| GitHub Actions | GitLab CI/CD | 说明 |
|----------------|--------------|------|
| `${{ github.run_number }}` | `${CI_PIPELINE_ID}` | 构建编号 |
| `${{ github.sha }}` | `${CI_COMMIT_SHA}` | 完整 commit hash |
| `${{ github.sha }}` | `${CI_COMMIT_SHORT_SHA}` | 短 commit hash |
| `${{ github.ref_name }}` | `${CI_COMMIT_REF_NAME}` | 分支名 |
| `${{ github.repository }}` | `${CI_PROJECT_PATH}` | 仓库路径 |
| `${{ github.actor }}` | `${GITLAB_USER_NAME}` | 触发用户 |
| `${{ secrets.GITHUB_TOKEN }}` | `${CI_JOB_TOKEN}` | 认证令牌 |

### 9. 失败处理

**GitHub Actions:**
```yaml
continue-on-error: true  # 允许失败
```

**GitLab CI/CD:**
```yaml
allow_failure: true      # 允许失败
```

### 10. 依赖管理

**GitHub Actions:**
```yaml
# GitHub Actions 步骤按顺序执行
steps:
  - name: Step 1
  - name: Step 2  # 自动依赖 Step 1
```

**GitLab CI/CD:**
```yaml
# GitLab 需要显式声明依赖
kicad-export:
  stage: build
  dependencies:
    - install-kicad  # 显式依赖
```

## GitLab 特有功能

### 1. 多阶段流水线
```yaml
stages:
  - setup
  - build
  - test
  - deploy
```

### 2. Job 之间依赖
```yaml
job-b:
  dependencies:
    - job-a
  needs:
    - job-a  # 不等待同阶段其他 job
```

### 3. 缓存策略
```yaml
cache:
  policy: pull        # 只拉取
  policy: push        # 只推送
  policy: pull-push   # 拉取并推送（默认）
```

### 4. 产物过期时间
```yaml
artifacts:
  expire_in: 1 week   # 1周后自动删除
```

### 5. 内置 Release 功能
```yaml
release:
  tag_name: "v1.0.0"
  name: "Release 1.0.0"
  description: "Release notes"
```

## GitHub Actions 特有功能

### 1. Actions Marketplace
```yaml
- uses: actions/checkout@v4      # 使用社区 Action
- uses: actions/upload-artifact@v4
```

### 2. 矩阵构建
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python: [3.8, 3.9, 3.10]
```

### 3. Workflow 复用
```yaml
uses: ./.github/workflows/reusable-workflow.yml
```

## 使用建议

### GitHub 项目使用：
- 文件：`.github/workflows/kicad-ci.yml`
- 特点：集成 GitHub 生态，Actions Marketplace 丰富

### GitLab 项目使用：
- 文件：`.gitlab-ci.yml`
- 特点：功能更强大，支持复杂流水线，缓存更灵活

### 配置差异总结：

| 功能 | GitHub | GitLab | 复杂度 |
|------|--------|--------|--------|
| **配置文件** | `.github/workflows/*.yml` | `.gitlab-ci.yml` | GitLab 更简单 |
| **变量语法** | `${{ }}` | `${}` | GitLab 更简单 |
| **阶段管理** | jobs 隐式串行 | stages 显式定义 | GitLab 更清晰 |
| **缓存机制** | 通过 Action | 内置支持 | GitLab 更方便 |
| **产物管理** | 通过 Action | 内置支持 | GitLab 更方便 |
| **Release** | 通过第三方 Action | 内置支持 | GitLab 更方便 |
| **社区资源** | Actions Marketplace | 较少 | GitHub 更丰富 |

## 迁移提示

如果你从 GitHub 迁移到 GitLab：

1. **重命名文件**：`.github/workflows/kicad-ci.yml` → `.gitlab-ci.yml`
2. **修改语法**：`env:` → `variables:`，`${{ }}` → `${}`
3. **定义阶段**：添加 `stages:` 定义
4. **调整 Actions**：使用 GitLab 内置功能替代 GitHub Actions
5. **测试流水线**：在 GitLab 上提交代码触发测试

如果你同时维护两个平台，可以保留两个配置文件，它们会各自独立工作。
