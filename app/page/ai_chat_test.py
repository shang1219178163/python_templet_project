from datetime import datetime
from typing import cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall

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
        """思考模式下带回完整助手消息，否则带 tools 的后续请求会 400"""
        for _ in range(5):
            response = self.clent.chat.completions.create(
                model="deepseek-flash",
                messages=self.messages,
                tools=self.tool_registry.definitions(),
                stream=False,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )
            message = response.choices[0].message
            # model_dump 保留 reasoning_content，思考模式带 tools 时必须原样回传
            self.messages.append(cast(ChatCompletionMessageParam, cast(object, message.model_dump(exclude_none=True))))
            if not message.tool_calls:
                print(f"回答:{message.content}")
                return

            for tool in message.tool_calls:
                if isinstance(tool, ChatCompletionMessageFunctionToolCall):
                    result = self.tool_registry.execute(tool.function.name, tool.function.arguments)
                    print(f"工具 {tool.function.name}({tool.function.arguments}) -> {result}")
                else:
                    result = "不支持的工具类型"
                self.messages.append({"role": "tool", "tool_call_id": tool.id, "content": result})

        print("<<<回答:工具调用次数过多，已停止")


if __name__ == "__main__":
    AIChatTest().run()
