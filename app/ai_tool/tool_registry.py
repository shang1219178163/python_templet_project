"""AI 工具核心：工具基类、HTTP 客户端与注册表。"""

import json
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from http.cookiejar import CookieJar
from json import JSONDecodeError
from typing import IO, Any, ClassVar, Self
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from openai.types.chat import ChatCompletionToolParam


class ToolError(RuntimeError):
    """工具执行中可预期的失败（网络、响应格式等），消息会原样交给模型。"""


class BaseTool(ABC):
    """一个可被模型调用的函数工具。

    子类填好 name / description / parameters 并实现 run；
    name 必须与模型发起的函数调用名一致，ToolRegistry 按它分发。
    """

    name: ClassVar[str]
    description: ClassVar[str]
    parameters: ClassVar[dict[str, Any]]

    def definition(self) -> ChatCompletionToolParam:
        """OpenAI 格式的函数定义，直接放进请求的 tools 参数"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """执行工具并返回给模型的文本；参数由模型生成，需自行校验。"""


class NetClient:
    """HTTP 请求客户端，供各 AI 工具持有。

    timeout 在构造时确定：天气接口响应快，搜索页相对慢，各工具按需传入。
    每个实例维护独立的 Cookie 会话，供 12306 这类要求先取会话再查询的站点使用。
    """

    USER_AGENT = "Mozilla/5.0"

    def __init__(self, timeout: float = 10) -> None:
        self.timeout = timeout
        self._opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def fetch_json(self, url: str, params: Mapping[str, str]) -> dict[str, Any]:
        """GET 一个接口并解析成 JSON 对象"""
        with self._open(f"{url}?{urlencode(params)}") as resp:
            try:
                data = json.loads(resp.read())
            except ValueError as err:  # JSONDecodeError / UnicodeDecodeError
                raise ToolError(f"接口返回的不是合法 JSON: {err}") from err
        if not isinstance(data, dict):
            raise ToolError("接口返回的不是 JSON 对象")
        return data

    def fetch_text(
        self,
        url: str,
        form: Mapping[str, str] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        """请求网页：form 非空时按表单 POST，否则 GET"""
        body = urlencode(form).encode() if form else None
        merged = {"User-Agent": self.USER_AGENT, **(headers or {})}
        if body is not None:
            merged["Content-Type"] = "application/x-www-form-urlencoded"
        with self._open(Request(url, data=body, headers=merged)) as resp:
            return resp.read().decode("utf-8", "replace")

    def _open(self, request: str | Request) -> IO[bytes]:
        """统一把网络层异常收成 ToolError"""
        if isinstance(request, str):
            request = Request(request, headers={"User-Agent": self.USER_AGENT})
        try:
            return self._opener.open(request, timeout=self.timeout)
        except OSError as err:  # URLError / HTTPError / TimeoutError 都是 OSError 子类
            raise ToolError(f"网络请求失败: {err}") from err


class ToolRegistry:
    """持有全部工具实例，是对话循环唯一需要接触的工具入口。"""

    def __init__(self, tools: Iterable[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or ():
            self.register(tool)

    def register(self, tool: BaseTool) -> Self:
        """注册工具；重名直接报错，避免调用时路由到错误的实现"""
        if tool.name in self._tools:
            raise ValueError(f"工具名重复: {tool.name}")
        self._tools[tool.name] = tool
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
