"""流式回答的分片累积测试（离线，不发起请求）。

运行方式（项目根目录）：
    python -m unittest tests.test_ai_chat_stream -v
"""

import io
import unittest
from contextlib import redirect_stdout

from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Choice,
    ChoiceDelta,
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)

from app.page.ai_chat.stream import consume_stream


def chunk(delta: ChoiceDelta) -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id="c",
        created=0,
        model="deepseek-flash",
        object="chat.completion.chunk",
        choices=[Choice(index=0, delta=delta, finish_reason=None)],
    )


def tool_part(index: int, *, id: str | None = None, name: str | None = None, arguments: str | None = None):
    return ChoiceDeltaToolCall(
        index=index,
        id=id,
        type="function" if id else None,
        function=ChoiceDeltaToolCallFunction(name=name, arguments=arguments),
    )


class ConsumeTest(unittest.TestCase):
    def consume(self, *chunks: ChatCompletionChunk) -> tuple[dict, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            message = consume_stream(chunks)
        return message, output.getvalue()

    def test_text_stream_assembled(self) -> None:
        message, output = self.consume(chunk(ChoiceDelta(content="你")), chunk(ChoiceDelta(content="好")))
        self.assertEqual(message["content"], "你好")
        self.assertEqual(output, "回答: 你好")

    def test_reasoning_content_kept(self) -> None:
        message, output = self.consume(
            chunk(ChoiceDelta(reasoning_content="先判断")),
            chunk(ChoiceDelta(content="答案")),
        )
        self.assertEqual(message["reasoning_content"], "先判断")
        self.assertEqual(message["content"], "答案")
        self.assertIn("思考: 先判断", output)

    def test_non_string_reasoning_ignored(self) -> None:
        message, _ = self.consume(
            chunk(ChoiceDelta(reasoning_content=123)),
            chunk(ChoiceDelta(content="ok")),
        )
        self.assertNotIn("reasoning_content", message)
        self.assertEqual(message["content"], "ok")

    def test_tool_call_fragments_merged(self) -> None:
        message, _ = self.consume(
            chunk(
                ChoiceDelta(
                    content=None,
                    tool_calls=[tool_part(0, id="call_1", name="get_weather", arguments='{"loc')],
                )
            ),
            chunk(ChoiceDelta(content=None, tool_calls=[tool_part(0, arguments='ation": "杭州"}')])),
        )
        self.assertIsNone(message["content"])
        self.assertEqual(
            message["tool_calls"],
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"location": "杭州"}'},
                }
            ],
        )

    def test_multiple_tool_calls_ordered(self) -> None:
        message, _ = self.consume(
            chunk(ChoiceDelta(content=None, tool_calls=[tool_part(1, id="b", name="second")])),
            chunk(ChoiceDelta(content=None, tool_calls=[tool_part(0, id="a", name="first")])),
        )
        self.assertEqual([call["function"]["name"] for call in message["tool_calls"]], ["first", "second"])

    def test_empty_choices_skipped(self) -> None:
        empty = ChatCompletionChunk(
            id="c", created=0, model="deepseek-flash", object="chat.completion.chunk", choices=[]
        )
        message, output = self.consume(empty, chunk(ChoiceDelta(content="ok")))
        self.assertEqual(message["content"], "ok")
        self.assertEqual(output, "回答: ok")


if __name__ == "__main__":
    unittest.main()
