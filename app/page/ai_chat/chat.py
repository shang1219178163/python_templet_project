"""对话核心：持有模型客户端、工具与消息历史，处理一轮问答。"""

from typing import Any, cast

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
)

from app.ai_tool import (
    MCPToolManager,
    MeteoWeatherTool,
    OcrTool,
    RoutePlannerTool,
    ToolRegistry,
    TrainQueryTool,
    TrainStopsTool,
    WebSearchTool,
)
from app.config import settings
from app.page.ai_chat.prompt import build_system_prompt
from app.page.ai_chat.stream import consume_stream

MAX_TOOL_ROUNDS = 5


class AIChat:
    """一轮问答 = 流式请求 + 执行工具，直到模型给出最终回答。"""

    def __init__(self, *, client: OpenAI | None = None, mcp: MCPToolManager | None = None) -> None:
        """client / mcp 可注入，方便离线测试；默认按 settings 与配置文件创建"""
        self.client = client or OpenAI(
            api_key=settings.api_key,
            base_url="https://api.deepseek.com",
        )
        # 连不上的 MCP server 只告警，不影响本地工具；配置见 app/assets/mcp_servers.json
        self.mcp = mcp or MCPToolManager.from_file().start()
        self.tool_registry = ToolRegistry([
            MeteoWeatherTool(),
            WebSearchTool(),
            RoutePlannerTool(),
            TrainQueryTool(),
            TrainStopsTool(),
            OcrTool(),
            *self.mcp.tools(),
        ])
        self.messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=build_system_prompt()),
        ]

    def ask(self, question: str) -> None:
        """追加用户问题并回答"""
        self.messages.append({"role": "user", "content": question})
        self.reply()

    def reply(self) -> None:
        """流式输出；工具调用分片拼成完整助手消息再回传，思考模式下缺字段会 400"""
        for _ in range(MAX_TOOL_ROUNDS):
            stream = self.client.chat.completions.create(
                model="deepseek-flash",
                messages=self.messages,
                tools=self.tool_registry.definitions(),
                stream=True,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )
            message = consume_stream(stream)
            self.messages.append(cast(ChatCompletionMessageParam, message))
            print()

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return

            for tool in tool_calls:
                self.messages.append(self._run_tool(tool))

        print("<<<回答:工具调用次数过多，已停止")

    def _run_tool(self, tool: dict[str, Any]) -> ChatCompletionToolMessageParam:
        """执行一次工具调用并打印结果，返回可追加的 tool 消息"""
        if tool.get("type") != "function":
            result = "不支持的工具类型"
        else:
            function = tool["function"]
            result = self.tool_registry.execute(function["name"], function["arguments"])
            print(f"工具 {function['name']}({function['arguments']}) -> {result}")
        return {"role": "tool", "tool_call_id": tool["id"], "content": result}

    def close(self) -> None:
        """释放 MCP 连接与子进程"""
        self.mcp.close()
