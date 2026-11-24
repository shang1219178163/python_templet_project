# PyCharm 侧边栏 Claude Agent 一直显示「正在准备」排查报告

- 排查时间：2026-11-24 09:04–09:12
- 环境：PyCharm 2026.2（darwin-x86_64，macOS 24.2.0）
- 现象：侧边聊天的 Claude Agent 长时间停在「正在准备」，无法进入对话

## 一、结论

安装这次已经成功，卡住的是**登录授权**环节：PyCharm 在底部终端跑着
`claude auth login --console` 等用户授权，授权完成前侧边栏不会进入聊天。

## 二、日志时间线

日志文件：`~/Library/Logs/JetBrains/PyCharm2026.2/idea.log`

| 时间 | 事件 |
| --- | --- |
| 09:04:31 | 上一次 `npm install` **300 秒超时** → `AcpProcessLaunchException$ConfigResolutionFailed`，界面停在「正在准备」 |
| 09:08:01 | PyCharm 重新安装 `@agentclientprotocol/claude-agent-acp@0.110.0` |
| 09:10:22 | 安装成功，ACP 进程启动成功（`Process started with PID: 26469`） |
| 09:10:24 | ACP 握手完成，agent 返回 `authRequired`（需要登录） |
| 09:10:43 | `AuthHandlerDispatcher` 选择 `ShellTerminalAuthHandler`，在终端执行 `claude auth login --console`，日志停在 `Waiting for terminal authentication to complete...` |
| 09:12:21 | 登录进程 `claude auth login --console`（PID 26553）仍在等待，已等 1 分半 |

## 三、原因解释

### 1. 安装为什么慢

`@agentclientprotocol/claude-agent-acp` 会带一个 378MB 的原生 `claude` 二进制
（`@anthropic-ai/claude-agent-sdk-darwin-x64/claude`）。即使 `~/.npmrc` 已切换为
npmmirror，下载也要 2 分钟左右，而 PyCharm 的安装上限是 5 分钟，很容易超时。

本次已安装完整：`node_modules` 101 个包、约 394MB，日志显示
`npm package ... already installed`，不会再重装。

### 2. 为什么安装好了还要登录

PyCharm 启动 agent 时带了 `--hide-claude-auth` 参数。这是 Anthropic/JetBrains 的硬性限制：

- **第三方集成不允许用 claude.ai 订阅（Free/Pro/Max/Team）给 SDK 计费**
- 只接受 API key（Anthropic Console 按量计费）或 Enterprise 套餐

因此，基于订阅或中转登录的 Claude Code 凭据会被判定「未认证」，agent 只能退回到
Console 登录流程（`console-login`）。

## 四、处理方案

### 方案一：使用 API key（最对口）

1. PyCharm 底部会自动打开一个终端标签（名称类似 `Claude Agent` / `Local`），里面在跑
   `claude auth login --console`
2. 按提示在浏览器打开 URL，用 Anthropic **Console** 账号授权
3. 把返回的 code 粘贴回终端，登录完成后侧边栏会自动进入聊天

找不到该终端时：关掉它，回到侧边栏点重试/刷新，会再次弹出登录终端。

### 方案二：改用其他 agent

- 侧边栏切换为 JetBrains 自带的 **Junie**（随 AI 订阅可用）
- 或继续使用 Claude Code CLI / 插件式用法，其认证与 ACP agent 完全独立

### 方案三：使用中转/网关

若凭据形式为 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`（中转网关），把这两个环境变量
放进 PyCharm 的启动环境即可：

- 从终端 `open -a PyCharm` 启动
- 或写入 `~/.zshrc` 后重启 PyCharm

带网关 token 的 agent 会被判定为「非订阅计费」，从而绕过 `--hide-claude-auth` 的拦截。

## 五、关键路径速查

| 用途 | 路径 |
| --- | --- |
| 日志 | `~/Library/Logs/JetBrains/PyCharm2026.2/idea.log` |
| agent 安装目录 | `~/Library/Caches/JetBrains/PyCharm2026.2/acp-agents/claude-acp/0.110.0` |
| 内置 Node/npm | `~/Library/Caches/JetBrains/PyCharm2026.2/acp-agents/.runtimes/node/24.19.0/bin` |
| 已安装 agent 注册表 | `~/Library/Application Support/JetBrains/acp-agents/installed.json` |
| npm 源配置 | `~/.npmrc`（`registry=https://registry.npmmirror.com`） |

## 六、排查顺序建议

1. 看 `AcpPackageInstaller`：是否出现 `timed out after 300000ms`（安装超时）
2. 看 `AcpServerProcessHandlerImpl`：是否 `Process started with PID`（进程是否起来）
3. 看 `TerminalAuthHandler`：是否停在 `Waiting for terminal authentication to complete`（是否在等登录）
