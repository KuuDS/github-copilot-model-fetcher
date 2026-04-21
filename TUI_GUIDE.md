# Copilot TUI 使用指南

## 新功能概览

### 1. Python Copilot CLI 包装器 (`copilot_cli.py`)

通过 Python 调用 `gh copilot` 命令：

```python
from copilot_fetcher.copilot_cli import CopilotCLI

cli = CopilotCLI()

# 获取代码建议
suggestion = cli.suggest("Write a function to calculate fibonacci", language="python")
print(suggestion.text)

# 解释代码
explanation = cli.explain("def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)")
print(explanation.text)

# 发送聊天消息
response = cli.prompt("What are the best practices for Python error handling?")
print(response)

# 启动交互式 gh copilot
from copilot_fetcher.copilot_cli import run_copilot_interactive
run_copilot_interactive()  # 这会启动真正的 gh copilot TUI
```

### 2. 交互式 TUI 模式 (`tui.py`)

启动内置的交互式界面：

```bash
./run.sh tui
# 或
python -m copilot_fetcher tui
```

#### 可用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help` | 显示帮助信息 | `/help` |
| `/models` | 列出所有可用模型 | `/models` |
| `/model` | 切换模型 | `/model gpt-4o` |
| `/clear` | 清空聊天记录 | `/clear` |
| `/history` | 显示对话历史 | `/history` |
| `/exit` 或 `/quit` | 退出程序 | `/exit` |

#### 快捷键

- `Ctrl+C` / `Ctrl+D` - 退出
- `Ctrl+L` - 清屏
- `↑/↓` - 浏览历史记录
- `Tab` - 命令补全

### 3. GitHub Actions 改进

Workflow 现在提供更好的错误处理：

- 详细的日志记录
- 成功/失败的状态输出
- Workflow Summary 显示结果
- 当 PAT 认证失败时提供清晰的错误信息和替代方案

#### 运行 workflow：

```bash
# 手动触发
gh workflow run daily-fetch.yml --repo KuuDS/github-copilot-model-fetcher

# 查看运行状态
gh run list --repo KuuDS/github-copilot-model-fetcher
```

## 已知限制

### GitHub Actions 中的 Copilot API

**问题**：Personal Access Token (PAT) 无法访问 Copilot API `/models` 端点

**原因**：
- Copilot API 需要特殊的内部令牌
- 该令牌只能通过交互式 `gh auth login` 获取
- PAT 在非交互式环境（如 GitHub Actions）中无法转换为内部令牌

**解决方案**：
1. **本地定时任务**（推荐）
   ```bash
   # 添加到 crontab，每天午夜运行
   0 0 * * * cd /path/to/repo && ./run.sh fetch
   ```

2. **手动运行**
   ```bash
   gh auth login  # 交互式认证
   ./run.sh fetch
   ```

3. **自托管 runner**
   - 配置带有预认证 gh CLI 的自托管 runner
   - 使用该 runner 运行 workflow

## 项目结构更新

```
src/copilot_fetcher/
├── __init__.py          # 包入口
├── __main__.py          # CLI 入口（添加了 tui 命令）
├── api.py               # Copilot API 客户端
├── copilot_cli.py       # 新增: gh copilot CLI 包装器
├── gh_auth.py           # GitHub CLI 认证
├── storage.py           # 数据存储
└── tui.py               # 新增: 交互式 TUI
```

## 依赖更新

`pyproject.toml` 中添加了以下依赖：
- `rich>=13.0.0` - 漂亮的终端 UI
- `prompt-toolkit>=3.0.0` - 交互式提示符

安装更新：
```bash
uv pip install -e .
# 或
pip install -e .
```

## 示例使用场景

### 场景 1：探索可用模型

```bash
./run.sh tui
# 然后输入:
/models
/model claude-sonnet-4.5
/exit
```

### 场景 2：获取代码建议

```python
from copilot_fetcher.copilot_cli import CopilotCLI

cli = CopilotCLI()
result = cli.suggest(
    "Create a Python decorator for retrying failed function calls",
    language="python"
)
print(result.text)
```

### 场景 3：本地自动化

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias copilot-fetch='cd ~/github-copilot-model-fetcher && ./run.sh fetch && ./run.sh list'

# 或者使用 cron（每天凌晨 2 点）
0 2 * * * /path/to/github-copilot-model-fetcher/run.sh fetch >> /var/log/copilot-fetch.log 2>&1
```

## 故障排除

### TUI 无法启动

```bash
# 确保依赖已安装
pip install rich prompt-toolkit

# 检查 gh CLI 认证
gh auth status
```

### GitHub Actions 失败

这是预期行为（PAT 限制）。查看 workflow summary 获取详细信息。

### gh copilot 命令不可用

```bash
# 安装 gh CLI
# macOS
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# 安装 Copilot 扩展
gh extension install github/gh-copilot
```

## 提交记录

```
d6236d9 feat: add Copilot TUI and improve GitHub Actions workflow
01411fc fix(actions): escape quotes in workflow summary
```
