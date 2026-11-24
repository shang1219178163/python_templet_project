"""工具注册表：汇总函数定义、按名字分发，并把失败转成文本交给模型。"""

import json
from collections.abc import Iterable
from json import JSONDecodeError
from typing import Self

from openai.types.chat import ChatCompletionToolParam

from app.ai_tool.base_tool import BaseTool, ToolError


class ToolRegistry:
    """持有全部工具实例，是对话循环唯一需要接触的工具入口。"""

    def __init__(self, tools: Iterable[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or ():
            self.register(tool)

    def register(self, tool: BaseTool) -> Self:
        """注册工具；重名直接报错，避免调用时路由到错误的实现"""
        if tool.NAME in self._tools:
            raise ValueError(f"工具名重复: {tool.NAME}")
        self._tools[tool.NAME] = tool
        return self

    def definitions(self) -> list[ChatCompletionToolParam]:
        """给模型声明全部可用工具"""
        return [tool.definition() for tool in self._tools.values()]

    def execute(self, name: str, arguments: str) -> str:
        """执行一次工具调用；任何问题都以文本返回，保证对话循环不中断"""
        tool = self._tools.get(name)
        if tool is None:
            return f"未知工具: {name}"
        try:
            args = json.loads(arguments or "{}")
        except JSONDecodeError:
            return "参数不是合法 JSON"
        if not isinstance(args, dict):
            return "参数必须是 JSON 对象"
        try:
            return tool.run(**args)
        except ToolError as err:
            return str(err)
        except Exception as err:  # 模型给的参数形状不可控，兜底回给模型继续对话
            return f"工具 {name} 执行失败: {err}"
