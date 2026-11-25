# AI 对话示例

流式回答 + 本地函数工具 + MCP 远程工具的最小对话循环。

## 目录结构

```
app/page/ai_chat/
├── __init__.py   # 包入口，导出 AIChat
├── chat.py       # AIChat：模型客户端、工具注册表、消息历史与问答循环
├── stream.py     # consume_stream：流式分片累积、思考/正文打印
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
| `chat.py` | `AIChat.reply()` 循环：流式请求 → 有 `tool_calls` 就执行并回传 → 直到最终回答；最多 5 轮 |
| `stream.py` | 把分片拼成完整助手消息：`reasoning_content`、`content` 分别拼接，`tool_calls` 按 index 合并；同时打印到终端 |
| `prompt.py` | 系统提示词，每次构造对话时生成，时间不会过期 |
| `main.py` | `input()` 循环，Ctrl-D / Ctrl-C 退出，退出前关闭 MCP 连接 |

## 扩展

- 新增本地工具：在 `app/ai_tool` 里实现 `BaseTool` 子类，然后加进 `chat.py` 的工具列表。
- 新增 MCP server：改 `app/assets/mcp_servers.json`，无需改代码。
- 换模型：改 `chat.py` 的 `model` 与 `base_url`；流式累积逻辑与模型无关。

## 测试

```bash
python -m unittest tests.test_ai_chat tests.test_ai_chat_stream -v
```

全部离线：用假客户端注入预置分片，不发起真实请求。
