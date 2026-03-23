# GitHub Copilot Model Fetcher

使用 OAuth 2.0 Device Flow 获取 GitHub Copilot 可用模型列表的 Python 工具。

## 功能

- OAuth 2.0 Device Flow 认证
- 获取 GitHub Copilot 模型列表
- 本地 JSON 存储
- 命令行工具

## 安装

```bash
# 使用 uv 安装依赖
uv pip install -e .

# 或使用 pip
pip install -e .
```

## 配置

### 1. 创建 GitHub OAuth App

1. 访问 https://github.com/settings/applications/new
2. 填写应用信息：
   - Application name: `Copilot Model Fetcher`
   - Homepage URL: `http://localhost`
   - Authorization callback URL: `http://localhost/callback`
3. 点击 **Register application**
4. 在应用设置中，勾选 **Enable Device Flow**
5. 记下 **Client ID** (不需要 Client Secret)

### 2. 设置环境变量

```bash
export GITHUB_CLIENT_ID="Ov23lixxxxxxxxxxxx"
```

或将此行添加到 `~/.bashrc` 或 `~/.zshrc`

## 使用方法

### 认证

```bash
python -m copilot_fetcher auth
```

这将：
1. 打开浏览器显示 GitHub 设备授权页面
2. 在终端显示授权码
3. 等待你在浏览器中输入授权码
4. 完成后保存访问令牌

### 获取模型列表

```bash
python -m copilot_fetcher fetch
```

这会获取所有可用的 Copilot 模型并保存到 `~/.copilot-fetcher/models.json`

### 查看模型列表

```bash
python -m copilot_fetcher list
```

输出示例：

```
================================================================================
GitHub Copilot Models (fetched: 2024-01-15T10:30:00)
================================================================================

1. GPT-4
   ID: gpt-4
   Version: 2024-01-01
   Provider: OpenAI
   Description: GPT-4 model for code completion
   Capabilities: code-completion, chat

2. Claude 3.5 Sonnet
   ID: claude-3.5-sonnet
   Version: 2024-06-20
   Provider: Anthropic
   Description: Claude 3.5 Sonnet for Copilot
   Capabilities: code-completion, chat, vision

================================================================================
Total: 15 models
================================================================================
```

### 查看原始 JSON

```bash
python -m copilot_fetcher raw
```

### 清除存储的数据

```bash
python -m copilot_fetcher clear
```

## 存储位置

默认数据存储在 `~/.copilot-fetcher/`：

- `token.json` - OAuth 访问令牌（权限 600）
- `models.json` - 获取的模型列表

## API 参考

### Python API

```python
from copilot_fetcher import CopilotClient, get_access_token

# 获取访问令牌
token = get_access_token("your_client_id")

# 使用客户端
with CopilotClient(token) as client:
    response = client.get_models()
    for model in response.models:
        print(f"{model.name}: {model.id}")
```

### 模块

- `copilot_fetcher.oauth` - OAuth 2.0 Device Flow 实现
- `copilot_fetcher.api` - GitHub Copilot API 客户端
- `copilot_fetcher.storage` - 本地数据存储

## OAuth 流程说明

本工具使用 [OAuth 2.0 Device Authorization Grant](https://tools.ietf.org/html/rfc8628)（设备流）：

1. 应用向 GitHub 请求设备代码和用户代码
2. GitHub 返回设备代码、用户代码和验证 URI
3. 应用显示用户代码，引导用户访问验证 URI
4. 用户在浏览器中输入用户代码并授权
5. 应用轮询令牌端点直到获得访问令牌
6. 使用访问令牌调用 Copilot API

## 故障排除

### "GITHUB_CLIENT_ID environment variable not set"

设置环境变量：
```bash
export GITHUB_CLIENT_ID="your_client_id"
```

### "Device code expired"

用户在规定时间内未完成授权。重新运行认证命令。

### "User denied authorization"

用户在 GitHub 页面上点击了拒绝。重新运行认证命令。

### API 错误

确保你的 GitHub 账户有 Copilot 订阅，并且 OAuth App 已正确配置。

## 项目结构

```
.
├── src/
│   └── copilot_fetcher/
│       ├── __init__.py      # 包入口
│       ├── __main__.py      # CLI 入口
│       ├── oauth.py         # OAuth 实现
│       ├── api.py           # API 客户端
│       └── storage.py       # 数据存储
├── pyproject.toml           # 项目配置
└── README.md               # 本文档
```

## License

MIT
