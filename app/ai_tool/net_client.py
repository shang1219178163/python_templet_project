"""工具共用的 HTTP 请求客户端：统一 User-Agent 与超时，并把网络异常转成 ToolError。"""

import json
from collections.abc import Mapping
from typing import IO, Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.ai_tool.base_tool import ToolError


class NetClient:
    """无状态的 HTTP 请求客户端，供各 AI 工具持有。

    timeout 在构造时确定：天气接口响应快，搜索页相对慢，各工具按需传入。
    """

    USER_AGENT = "Mozilla/5.0"

    def __init__(self, timeout: float = 10) -> None:
        self.timeout = timeout

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
        try:
            return urlopen(request, timeout=self.timeout)
        except OSError as err:  # URLError / HTTPError / TimeoutError 都是 OSError 子类
            raise ToolError(f"网络请求失败: {err}") from err
