"""Anthropic 兼容接口调用：消息构造与流式输出。"""

from __future__ import annotations

import base64
import os
from collections.abc import Iterator
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from file_reader import image_media_type

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "deepseek-chat")
VISION_MODEL = os.getenv("ANTHROPIC_VISION_MODEL") or MODEL
SYSTEM_PROMPT = "你是资深软件工程师,请用中文回答我的问题"
MAX_TOKENS = 8192

client = anthropic.Anthropic()


def build_messages(history: list[dict], data_dir: Path) -> list[dict]:
    """把存储的消息转换为 Anthropic messages。"""
    messages = []
    for message in history:
        if message["role"] == "assistant":
            messages.append(
                {
                    "role": "assistant",
                    "content": message["model_text"] or message["text"],
                }
            )
            continue

        blocks = []
        for attachment in message["attachments"]:
            if attachment.get("kind") != "image":
                continue
            path = data_dir / attachment["path"]
            if not path.exists():
                continue
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type(attachment["name"]),
                        "data": base64.standard_b64encode(path.read_bytes()).decode(),
                    },
                }
            )

        text = message["model_text"] or message["text"]
        if blocks:
            if text:
                blocks.append({"type": "text", "text": text})
            messages.append({"role": "user", "content": blocks})
        elif text:
            messages.append({"role": "user", "content": text})
    return messages


def pick_model(messages: list[dict]) -> str:
    """含图片时使用视觉模型，否则使用文本模型。"""
    return VISION_MODEL if _has_image(messages) else MODEL


def stream_reply(messages: list[dict]) -> Iterator[str]:
    """流式生成回答。"""
    model = pick_model(messages)
    with client.messages.stream(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        yield from stream.text_stream


def _has_image(messages: list[dict]) -> bool:
    for message in messages:
        content = message["content"]
        if isinstance(content, list) and any(
            block.get("type") == "image" for block in content
        ):
            return True
    return False


def format_api_error(exc: Exception) -> str:
    """把 SDK 异常转换为中文提示。"""
    if isinstance(exc, anthropic.AuthenticationError):
        return "鉴权失败：请检查 .env 中的 ANTHROPIC_AUTH_TOKEN 是否正确。"
    if isinstance(exc, anthropic.NotFoundError):
        return (
            "模型或接口不存在：请检查 ANTHROPIC_BASE_URL 与模型名"
            f"（{MODEL} / {VISION_MODEL}）。"
        )
    if isinstance(exc, anthropic.RateLimitError):
        return "请求过于频繁，请稍后重试。"
    if isinstance(exc, anthropic.APIConnectionError):
        return "网络连接失败：请检查 ANTHROPIC_BASE_URL 是否可访问。"
    if isinstance(exc, anthropic.APIStatusError):
        return f"接口返回异常（HTTP {exc.status_code}）：{exc.message}"
    return f"请求失败（{type(exc).__name__}）：{exc}"
