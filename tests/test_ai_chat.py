"""AIChat 对话循环测试（离线，不发起请求）。

运行方式（项目根目录）：
    python -m unittest tests.test_ai_chat -v
"""

import io
import unittest
from types import SimpleNamespace
from typing import Any

from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Choice,
    ChoiceDelta,
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)

from app.ai_tool import BaseTool, MCPToolManager, ToolRegistry
from app.page.ai_chat.chat import AIChat, _system_prompt
from app.page.ai_chat.stream import StreamConsumer


def chunk(delta: ChoiceDelta) -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id="c",
        created=0,
        model="deepseek-flash",
        object="chat.completion.chunk",
        choices=[Choice(index=0, delta=delta, finish_reason=None)],
    )


def tool_call_chunk(name: str, arguments: str, call_id: str = "call_1") -> ChatCompletionChunk:
    return chunk(
        ChoiceDelta(
            content=None,
            tool_calls=[
                ChoiceDeltaToolCall(
                    index=0,
                    id=call_id,
                    type="function",
                    function=ChoiceDeltaToolCallFunction(name=name, arguments=arguments),
                )
            ],
        ),
    )


class FakeCompletions:
    """按顺序交出预置的流，并记录每次请求参数"""

    def __init__(self, *streams: list[ChatCompletionChunk]) -> None:
        self.streams = list(streams)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> list[ChatCompletionChunk]:
        # 快照 messages：调用方之后还会继续追加，直接存引用会拿到后续状态
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.streams.pop(0)


class EchoTool(BaseTool):
    name = "echo"
    description = "回显参数"
    parameters = {"type": "object", "properties": {"text": {"type": "string"}}}

    def run(self, **kwargs: Any) -> str:
        return f"echo:{kwargs.get('text')}"


class ReplyLoopTest(unittest.TestCase):
    def make_chat(
        self, *streams: list[ChatCompletionChunk]
    ) -> tuple[AIChat, FakeCompletions, io.StringIO]:
        completions = FakeCompletions(*streams)
        output = io.StringIO()
        chat = AIChat(
            client=SimpleNamespace(chat=SimpleNamespace(completions=completions)),
            mcp=MCPToolManager(),
            consumer=StreamConsumer(out=output),
        )
        chat.tool_registry = ToolRegistry([EchoTool()])
        chat.messages.append({"role": "user", "content": "试试"})
        return chat, completions, output

    def test_tool_round_then_answer(self) -> None:
        chat, _, output = self.make_chat(
            [tool_call_chunk("echo", '{"text": "hi"}')],
            [chunk(ChoiceDelta(content="好的")), chunk(ChoiceDelta(content="，收到"))],
        )
        chat.reply()

        self.assertEqual([m["role"] for m in chat.messages], ["system", "user", "assistant", "tool", "assistant"])
        self.assertEqual(chat.messages[3]["content"], "echo:hi")
        self.assertEqual(chat.messages[4]["content"], "好的，收到")
        self.assertIn("工具 echo", output.getvalue())

    def test_second_request_contains_tool_result(self) -> None:
        chat, completions, _ = self.make_chat(
            [tool_call_chunk("echo", '{"text": "hi"}')],
            [chunk(ChoiceDelta(content="完成"))],
        )
        chat.reply()

        self.assertEqual(len(completions.calls), 2)
        request_messages = completions.calls[1]["messages"]
        self.assertEqual([m["role"] for m in request_messages], ["system", "user", "assistant", "tool"])

    def test_direct_answer_stops_after_one_request(self) -> None:
        chat, completions, _ = self.make_chat([chunk(ChoiceDelta(content="直接回答"))])
        chat.reply()

        self.assertEqual(len(completions.calls), 1)
        self.assertEqual(chat.messages[-1]["content"], "直接回答")

    def test_tool_round_limit(self) -> None:
        streams = [[tool_call_chunk("echo", "{}")] for _ in range(6)]
        chat, completions, output = self.make_chat(*streams)
        chat.reply()

        self.assertEqual(len(completions.calls), 5)
        self.assertIn("工具调用次数过多", output.getvalue())


class SystemPromptTest(unittest.TestCase):
    def test_lists_registered_tools(self) -> None:
        prompt = _system_prompt(ToolRegistry([EchoTool()]))
        self.assertIn("- echo：回显参数", prompt)
        self.assertIn("当前时间是", prompt)

    def test_empty_registry(self) -> None:
        prompt = _system_prompt(ToolRegistry())
        self.assertIn("可按需调用以下工具", prompt)


if __name__ == "__main__":
    unittest.main()
