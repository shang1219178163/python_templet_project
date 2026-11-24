"""工具基类：统一工具名、描述与参数 Schema，模型据此决定何时调用。"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from openai.types.chat import ChatCompletionToolParam


class ToolError(RuntimeError):
    """工具执行中可预期的失败（网络、响应格式等），消息会原样交给模型。"""


class BaseTool(ABC):
    """一个可被模型调用的函数工具。

    子类填好 NAME / DESCRIPTION / PARAMETERS 并实现 run；
    NAME 必须与模型发起的函数调用名一致，ToolRegistry 按它分发。
    """

    NAME: ClassVar[str]
    DESCRIPTION: ClassVar[str]
    PARAMETERS: ClassVar[dict[str, Any]]

    def definition(self) -> ChatCompletionToolParam:
        """OpenAI 格式的函数定义，直接放进请求的 tools 参数"""
        return {
            "type": "function",
            "function": {
                "name": self.NAME,
                "description": self.DESCRIPTION,
                "parameters": self.PARAMETERS,
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """执行工具并返回给模型的文本；参数由模型生成，需自行校验。"""
