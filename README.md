# GitHub Copilot Model Fetcher

获取 GitHub Copilot 可用模型列表的 Python 工具。

支持两种认证方式：
- **GitHub CLI (gh)** - 推荐，获取完整模型列表 (35+)
- **OAuth Device Flow** - 备选，获取基础模型列表 (7)

## 功能

- 双模式认证：GitHub CLI 或 OAuth Device Flow
- 获取 GitHub Copilot 完整模型列表（Claude, GPT-5, Gemini, Grok）
- 按提供商分组显示模型
- 本地 JSON 存储
- 命令行工具

## 安装

```bash
# 克隆仓库
git clone https://github.com/KuuDS/github-copilot-model-fetcher.git
cd github-copilot-model-fetcher

# 使用 uv 安装依赖
uv pip install -e .

# 或使用 pip
pip install -e .
```

## 快速开始（推荐方式）

使用 **GitHub CLI** 获取完整模型列表（35+ 模型）：

```bash
# 1. 安装 GitHub CLI（如果尚未安装）
# https://cli.github.com/

# 2. 登录 GitHub
gh auth login

# 3. 获取模型列表
./run.sh fetch

# 4. 查看模型
./run.sh list
```

## 支持的模型

使用 GitHub CLI 认证可获取完整模型列表：

### Anthropic Claude
- Claude Opus 4.5, 4.6
- Claude Sonnet 4, 4.5, 4.6
- Claude Haiku 4.5

### OpenAI GPT
- GPT-4.1 系列
- GPT-5 系列（5-mini, 5.1, 5.2, 5.4 等）
- GPT-5 Codex 系列（5.1-codex, 5.2-codex, 5.3-codex 等）
- GPT-4o 系列

### Google Gemini
- Gemini 2.5 Pro

### xAI Grok
- Grok Code Fast 1

### 嵌入模型
- text-embedding-3-small
- text-embedding-ada-002

## 认证方式

### 方式 1：GitHub CLI（推荐）

提供完整模型访问权限（35+ 模型）。

```bash
# 检查 gh CLI 状态
./run.sh status

# 获取模型
./run.sh fetch
```

**要求：**
- 安装 GitHub CLI: https://cli.github.com/
- 运行 `gh auth login` 完成认证
- 拥有 GitHub Copilot 订阅

### 方式 2：OAuth Device Flow

提供基础模型访问权限（7 个模型）。

```bash
# 1. 创建 GitHub OAuth App
# 访问 https://github.com/settings/applications/new
# - 启用 Device Flow
# - 记下 Client ID

# 2. 配置环境
cp set_env.sh.template set_env.sh
# 编辑 set_env.sh，填入你的 Client ID

# 3. 认证并获取模型
./run.sh auth
./run.sh fetch
./run.sh list
```

**注意：** OAuth 方式受限于 Copilot API 的访问策略，只能获取基础 GPT 模型。

## 使用方法

### 查看认证状态

```bash
./run.sh status
```

### 获取模型列表

```bash
# 使用 gh CLI（自动检测）
./run.sh fetch

# 强制重新认证
./run.sh fetch --force-auth
```

### 查看模型列表

```bash
./run.sh list
```

输出示例：

```
================================================================================
GitHub Copilot Models (fetched: 2026-03-23T16:28:24)
================================================================================

【Anthropic Claude】
  • claude-opus-4.6
    (Claude Opus 4.6)
  • claude-sonnet-4.6
    (Claude Sonnet 4.6)
  • ...

【OpenAI GPT】
  • gpt-5.4
    (GPT-5.4)
  • gpt-4.1
    (GPT-4.1)
  • gpt-4o
    (GPT-4o)
  • ...

【Google Gemini】
  • gemini-2.5-pro
    (Gemini 2.5 Pro)

【xAI Grok】
  • grok-code-fast-1
    (Grok Code Fast 1)

================================================================================
Total: 35 models
================================================================================
```

### 查看原始 JSON

```bash
./run.sh raw
```

### 清除存储的数据

```bash
./run.sh clear
```

## 存储位置

默认数据存储在 `~/.copilot-fetcher/`：

- `token.json` - 访问令牌（权限 600）
- `models.json` - 获取的模型列表

## API 参考

### Python API

```python
from copilot_fetcher import CopilotClient, get_gh_token

# 使用 GitHub CLI token（推荐）
token = get_gh_token()

# 使用客户端
with CopilotClient(token) as client:
    response = client.get_models()
    for model in response.models:
        print(f"{model.name}: {model.id}")
```

### 模块

- `copilot_fetcher.gh_auth` - GitHub CLI 认证
- `copilot_fetcher.oauth` - OAuth 2.0 Device Flow
- `copilot_fetcher.api` - GitHub Copilot API 客户端
- `copilot_fetcher.storage` - 本地数据存储

## 故障排除

### "GitHub CLI is not authenticated"

```bash
gh auth login
```

### 只能获取 7 个模型

这是 OAuth 认证的限制。使用 GitHub CLI 认证可获取 35+ 模型：

```bash
./run.sh clear  # 清除旧 token
./run.sh fetch  # 将自动使用 gh CLI
```

### "No models found"

运行获取命令：

```bash
./run.sh fetch
```

## 项目结构

```
.
├── src/
│   └── copilot_fetcher/
│       ├── __init__.py      # 包入口
│       ├── __main__.py      # CLI 入口
│       ├── gh_auth.py       # GitHub CLI 认证
│       ├── oauth.py         # OAuth 实现
│       ├── api.py           # API 客户端
│       └── storage.py       # 数据存储
├── set_env.sh.template      # 环境配置模板
├── run.sh                   # 启动脚本
├── pyproject.toml           # 项目配置
└── README.md               # 本文档
```

## 为什么有两种认证方式？

GitHub Copilot API 对不同类型的令牌返回不同的模型列表：

| 认证方式 | 模型数量 | 包含的模型 |
|---------|---------|-----------|
| GitHub CLI (`gh auth token`) | 35+ | Claude, GPT-5, Gemini, Grok, 等 |
| OAuth Device Flow | 7 | GPT-3.5, GPT-4o 基础模型 |

这是因为 Copilot API 的内部权限控制机制。GitHub CLI 使用的是特殊的内部令牌端点，可以访问完整的模型列表。

## License

MIT
