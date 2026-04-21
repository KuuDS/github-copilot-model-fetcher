# GitHub Actions 问题解决方案

## 🔴 问题根源

GitHub Copilot API (`api.githubcopilot.com/models`) **明确拒绝所有 Personal Access Tokens**:

```
HTTP 400: Personal Access Tokens are not supported for this endpoint
```

这是 GitHub 的**有意设计**，目的是：
1. 防止自动化工具滥用 Copilot API
2. 强制要求交互式设备授权流程
3. 控制对模型列表的访问权限

## ❌ 为什么这些方法都失败了

### 1. 直接 HTTP 请求 (httpx/requests)
```python
headers = {"Authorization": "Bearer ghp_xxx"}
# ❌ 结果: HTTP 400 - PAT not supported
```

### 2. GitHub CLI API 命令
```bash
gh api https://api.githubcopilot.com/models
# ❌ 结果: HTTP 400 - PAT not supported (gh CLI 底层也是 PAT)
```

### 3. GitHub CLI 交互式登录
```bash
echo "$GH_TOKEN" | gh auth login --with-token
# ❌ 结果: 登录成功，但获取的 token 仍然是 PAT 类型，无法访问 Copilot API
```

### 4. 内部令牌端点
```bash
gh api /copilot_internal/v2/token
# ❌ 结果: 404 或权限不足
```

## ✅ 可行的解决方案

### 方案 1：自托管 Runner (推荐用于 CI/CD)

**原理**: 在自有服务器上运行 GitHub Actions，预先完成 `gh auth login` 交互式认证。

**步骤**:

1. **准备服务器** (Ubuntu/Debian):
```bash
# 安装 GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# 交互式登录 (关键步骤！)
gh auth login
# 选择: GitHub.com -> HTTPS -> 浏览器登录 -> 授权

# 验证
gh auth status
```

2. **配置自托管 Runner**:
```bash
# 下载 runner
curl -o actions-runner-linux-x64-2.320.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.320.0/actions-runner-linux-x64-2.320.0.tar.gz
tar xzf actions-runner-linux-x64-2.320.0.tar.gz

# 配置 (使用你的仓库)
./config.sh --url https://github.com/KuuDS/github-copilot-model-fetcher --token YOUR_RUNNER_TOKEN

# 运行
./run.sh
```

3. **修改 Workflow**:
```yaml
jobs:
  fetch-models:
    runs-on: self-hosted  # 改为自托管 runner
    # ... 其他配置不变
```

**优点**:
- ✅ 完全自动化
- ✅ 可以访问完整模型列表
- ✅ 与 GitHub Actions 集成

**缺点**:
- ❌ 需要维护服务器
- ❌ 需要定期重新认证（令牌过期）

---

### 方案 2：本地定时任务 (推荐用于个人使用)

**原理**: 在本地机器上运行 `gh auth login`，然后使用 cron/systemd/launchd 定时执行。

**macOS (launchd)**:

1. 创建 plist 文件 `~/Library/LaunchAgents/com.copilot-fetch.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.copilot-fetch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/github-copilot-model-fetcher && ./run.sh fetch</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/copilot-fetch.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/copilot-fetch.error</string>
</dict>
</plist>
```

2. 加载服务:
```bash
launchctl load ~/Library/LaunchAgents/com.copilot-fetch.plist
launchctl start com.copilot-fetch
```

**Linux (systemd)**:

1. 创建 service 文件 `~/.config/systemd/user/copilot-fetch.service`:
```ini
[Unit]
Description=GitHub Copilot Model Fetcher
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/github-copilot-model-fetcher
ExecStart=/path/to/github-copilot-model-fetcher/run.sh fetch
StandardOutput=append:/var/log/copilot-fetch.log
StandardError=append:/var/log/copilot-fetch.error
```

2. 创建 timer 文件 `~/.config/systemd/user/copilot-fetch.timer`:
```ini
[Unit]
Description=Run Copilot Fetch daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. 启用:
```bash
systemctl --user daemon-reload
systemctl --user enable copilot-fetch.timer
systemctl --user start copilot-fetch.timer
```

**Linux (cron)**:

```bash
# 编辑 crontab
crontab -e

# 添加行 (每天凌晨 2 点运行)
0 2 * * * cd /path/to/github-copilot-model-fetcher && ./run.sh fetch >> /var/log/copilot-fetch.log 2>&1
```

**优点**:
- ✅ 简单可靠
- ✅ 利用现有的 gh CLI 认证
- ✅ 无需服务器

**缺点**:
- ❌ 电脑必须开机
- ❌ 不是真正的 CI/CD

---

### 方案 3：GitHub Codespaces (云开发环境)

**原理**: 使用 GitHub Codespaces 的预认证环境。

**步骤**:

1. 在仓库中创建 `.devcontainer/devcontainer.json`:
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "postCreateCommand": "pip install -e . && gh auth login",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
```

2. 启动 Codespace 并完成交互式 `gh auth login`

3. 在 Codespace 中设置定时任务（使用 cron）

**优点**:
- ✅ 云端运行，无需本地机器
- ✅ 与 GitHub 深度集成
- ✅ 免费额度通常足够

**缺点**:
- ❌ Codespace 停止后定时任务不运行
- ❌ 需要保持 Codespace 活跃

---

### 方案 4：GitHub App (需要开发)

**原理**: 创建一个 GitHub App 并使用 App 的令牌，而不是 PAT。

**可行性**: ⚠️ **不确定**

GitHub App 令牌可能有不同的权限模型，但不确定是否能访问 Copilot API。

**实现步骤**:
1. 在 GitHub 开发者设置中创建 GitHub App
2. 安装 App 到用户账户
3. 生成私钥并转换为令牌
4. 使用 App 令牌调用 API

**需要测试**才能确认是否可行。

---

## 🔧 技术细节：为什么不能自动化？

### 认证流程对比

**Personal Access Token (PAT)**:
```
GitHub Actions → GH_TOKEN (PAT) → api.githubcopilot.com
                                    ↓
                              ❌ HTTP 400
```

**Device Flow (交互式)**:
```
用户浏览器 → github.com/login/device → 授权
                                           ↓
gh CLI ← 设备令牌 ← GitHub
   ↓
gh auth token ← 内部令牌 ← api.github.com
   ↓
api.githubcopilot.com/models
   ↓
✅ 成功
```

### 关键区别

| 令牌类型 | 获取方式 | 访问 Copilot API | 自动化 |
|---------|---------|-----------------|--------|
| PAT | 手动生成 | ❌ 不支持 | ✅ 可以 |
| Device Flow | 交互式授权 | ✅ 支持 | ❌ 需要人工 |
| GitHub App | 私钥生成 | ❓ 未测试 | ✅ 可以 |
| OAuth App | 用户授权 | ❓ 未测试 | ⚠️ 需要刷新 |

## 📝 建议

对于你的使用场景，推荐优先级：

1. **个人使用**: 本地 cron/systemd + `gh auth login`
2. **团队协作**: 自托管 Runner
3. **云原生**: GitHub Codespaces + cron
4. **长期方案**: 测试 GitHub App 可行性

## ❓ 常见问题

**Q: 能否使用 selenium/playwright 自动浏览器登录？**
A: 技术上可行，但违反了 GitHub ToS，不建议使用。

**Q: 令牌多久过期？**
A: Device Flow 获取的令牌通常几个月有效，具体取决于 GitHub 策略。

**Q: 能否缓存模型列表避免频繁获取？**
A: 模型列表相对稳定，可以每天或每周获取一次即可。
