# AI 对话示例

流式回答 + 本地函数工具 + MCP 远程工具的最小对话循环。

## 目录结构

```
app/page/ai_chat/
├── __init__.py   # 包入口，导出 AIChat
├── chat.py       # AIChat：模型客户端、工具注册表、消息历史与问答循环
├── stream.py     # StreamConsumer：流式分片累积、思考/正文打印
├── config.py     # AIChatConfig：模型、接口地址与循环参数
├── prompt.py     # build_system_prompt：系统提示词（含当前时间）
└── main.py       # 命令行入口
```

## 运行

在项目根目录执行：

```bash
python -m app.page.ai_chat.main
```

需要 `.env` 里的 `API_KEY`（DeepSeek）。MCP server 配在 `app/assets/mcp_servers.json`，留空则只用本地工具。

## 各文件职责

| 文件 | 职责 |
| --- | --- |
| `chat.py` | `AIChat.reply()` 循环：流式请求 → 有 `tool_calls` 就执行并回传 → 直到最终回答；轮次上限来自配置 |
| `stream.py` | `StreamConsumer.consume()`：把分片拼成完整助手消息——`reasoning_content`、`content` 分别拼接，`tool_calls` 按 index 合并；同时打印到指定输出流 |
| `config.py` | `AIChatConfig`：模型、接口地址、推理强度、轮次上限、是否打印思考；支持环境变量覆盖 |
| `prompt.py` | 系统提示词，每次构造对话时生成，时间不会过期 |
| `main.py` | `input()` 循环，Ctrl-D / Ctrl-C 退出，退出前关闭 MCP 连接 |

## 配置

默认值在 `config.py`，临时改可在项目根 `.env` 里覆盖（`AI_CHAT_` 前缀）：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AI_CHAT_BASE_URL` | `https://api.deepseek.com` | 模型接口地址 |
| `AI_CHAT_MODEL` | `deepseek-flash` | 模型名 |
| `AI_CHAT_REASONING_EFFORT` | `high` | 推理强度：`none` / `minimal` / `low` / `medium` / `high` / `xhigh` / `max` |
| `AI_CHAT_MAX_TOOL_ROUNDS` | `5` | 一轮问答里最多连续调用工具的轮数 |
| `AI_CHAT_PRINT_THINKING` | `true` | 是否把思考内容打印到终端（关闭后仍会累积回传） |

API Key 仍用 `app.config.settings.api_key`（即 `.env` 里的 `API_KEY`），不在 `AIChatConfig` 里重复定义。

## 扩展

- 新增本地工具：在 `app/ai_tool` 里实现 `BaseTool` 子类，然后加进 `chat.py` 的工具列表。
- 新增 MCP server：改 `app/assets/mcp_servers.json`，无需改代码。
- 换模型：改 `.env` 的 `AI_CHAT_MODEL` / `AI_CHAT_BASE_URL`；流式累积逻辑与模型无关。
- 接入其他界面：构造 `AIChat(consumer=StreamConsumer(out=你的输出流))`，所有对话输出都会写到该流。

## 测试

```bash
python -m unittest tests.test_ai_chat tests.test_ai_chat_stream -v
```

全部离线：用假客户端注入预置分片，不发起真实请求。
