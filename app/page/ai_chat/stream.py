"""流式回答的分片累积与输出。"""

from collections.abc import Iterable
from typing import Any

from openai.types.chat.chat_completion_chunk import ChatCompletionChunk


def consume_stream(stream: Iterable[ChatCompletionChunk]) -> dict[str, Any]:
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
        # reasoning_content 是 SDK 透传的 extra 字段，先确认是字符串再拼接
        reasoning_text = getattr(delta, "reasoning_content", None)
        if isinstance(reasoning_text, str) and reasoning_text:
            if not thinking_shown:
                print("思考: ", end="", flush=True)
                thinking_shown = True
            print(reasoning_text, end="", flush=True)
            reasoning.append(reasoning_text)
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
