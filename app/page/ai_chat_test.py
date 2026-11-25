from collections.abc import Iterable
from datetime import datetime
from typing import Any, cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

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


class AIChatTest:
    SYSTEM_PROMPT = (f"你是超级助手。询问天气时调用 get_weather；"
                     f"需要新闻、最新事实或当前事件时调用 web_search; "
                     f"询问两地路线、距离、开车多久时调用 plan_route；"
                     f"查询火车车次、余票、发到时刻时调用 query_train，"
                     f"查询某趟车经停站时调用 query_train_stops；"
                     f"用户给出图片路径并要求识别图片文字时调用 ocr_image；"
                     f"当前时间是 {datetime.now():%Y-%m-%d %H:%M}。"
                     f"不要编造天气或实时信息。")

    def __init__(self) -> None:
        self.clent = OpenAI(
            api_key=settings.api_key,
            base_url="https://api.deepseek.com",
        )
        # 连不上的 MCP server 只告警，不影响本地工具；配置见 app/assets/mcp_servers.json
        self.mcp = MCPToolManager.from_file().start()
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
            ChatCompletionSystemMessageParam(role="system", content=self.SYSTEM_PROMPT),
        ]

    def run(self) -> None:
        try:
            while True:
                question = input(">> 问题: ").strip()
                if not question:
                    continue
                self.messages.append({"role": "user", "content": question})
                self.reply()
        except (EOFError, KeyboardInterrupt):
            print()
        finally:
            self.mcp.close()

    def reply(self) -> None:
        """流式输出；工具调用分片拼成完整助手消息再回传，思考模式下缺字段会 400"""
        for _ in range(5):
            stream = self.clent.chat.completions.create(
                model="deepseek-flash",
                messages=self.messages,
                tools=self.tool_registry.definitions(),
                stream=True,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )
            message = self._consume(stream)
            self.messages.append(cast(ChatCompletionMessageParam, message))
            print()

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return

            for tool in tool_calls:
                if tool.get("type") != "function":
                    result = "不支持的工具类型"
                else:
                    function = tool["function"]
                    result = self.tool_registry.execute(function["name"], function["arguments"])
                    print(f"工具 {function['name']}({function['arguments']}) -> {result}")
                self.messages.append({"role": "tool", "tool_call_id": tool["id"], "content": result})

        print("<<<回答:工具调用次数过多，已停止")

    @staticmethod
    def _consume(stream: Iterable[ChatCompletionChunk]) -> dict[str, Any]:
        """边打印边累积分片：思考与正文分别拼接，工具调用按 index 合并。

        思考模式下 reasoning_content 和 tool_calls 必须完整回传给下一轮请求，
        所以这里还原出与 stream=False 时同等结构的助手消息。
        """
        content: list[str] = []
        reasoning: list[str] = []
        calls: dict[int, dict[str, Any]] = {}
        thinking_shown = False
        answer_shown = False
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if text := getattr(delta, "reasoning_content", None):
                if not thinking_shown:
                    print("思考: ", end="", flush=True)
                    thinking_shown = True
                print(text, end="", flush=True)
                reasoning.append(text)
            if delta.content:
                if not answer_shown:
                    print("\n回答: " if thinking_shown else "回答: ", end="", flush=True)
                    answer_shown = True
                print(delta.content, end="", flush=True)
                content.append(delta.content)
            for part in delta.tool_calls or []:
                slot = calls.setdefault(
                    part.index or 0,
                    {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                )
                if part.id:
                    slot["id"] = part.id
                if part.function is not None:
                    slot["function"]["name"] += part.function.name or ""
                    slot["function"]["arguments"] += part.function.arguments or ""

        message: dict[str, Any] = {"role": "assistant", "content": "".join(content) or None}
        if reasoning:
            message["reasoning_content"] = "".join(reasoning)
        if calls:
            message["tool_calls"] = [calls[index] for index in sorted(calls)]
        return message


if __name__ == "__main__":
    AIChatTest().run()
