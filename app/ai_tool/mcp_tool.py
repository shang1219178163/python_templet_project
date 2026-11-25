"""MCP 适配层：把 MCP server 上的工具接进本地 ToolRegistry。

一个 server 一个后台线程：线程里跑 asyncio 事件循环，维持 stdio / Streamable HTTP 连接；
同步的 CLI 代码通过 ``MCPConnection.call_tool()`` 跨线程调用，不用把对话循环改成 async。

典型用法：
    manager = MCPToolManager.from_file()
    manager.start()
    registry = ToolRegistry([*local_tools, *manager.tools()])
    ...
    manager.close()
"""

import asyncio
import json
import sys
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any, Self

from mcp import Client, StdioServerParameters
from mcp import types as mcp_types
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, model_validator

from app.ai_tool.tool_registry import BaseTool, ToolError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "app" / "assets" / "mcp_servers.json"


class MCPServerConfig(BaseModel):
    """一个 MCP server 的连接配置：``url``（远程）与 ``command``（本地子进程）二选一。"""

    url: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None
    connect_timeout: float = 30
    call_timeout: float = 60

    @model_validator(mode="after")
    def _check_transport(self) -> Self:
        if bool(self.url) == bool(self.command):
            raise ValueError("url 与 command 必须且只能填一个")
        if self.url is not None and (self.args or self.env or self.cwd):
            raise ValueError("args/env/cwd 只能和 command 一起用")
        return self


class MCPConnection:
    """一个 MCP server 的连接：后台线程持有事件循环，对外只暴露同步方法。"""

    def __init__(
        self,
        name: str,
        config: MCPServerConfig,
        *,
        client_factory: Callable[[], Client] | None = None,
    ) -> None:
        self.name = name
        self.config = config
        self.tools: list[mcp_types.Tool] = []
        self._client_factory = client_factory or self._build_client
        self._client: Client | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stop: asyncio.Event | None = None
        self._error: Exception | None = None

    def _build_client(self) -> Client:
        if self.config.url is not None:
            return Client(self.config.url)
        params = StdioServerParameters(
            command=self.config.command or "",
            args=self.config.args,
            env=self.config.env,
            cwd=self.config.cwd,
        )
        return Client(stdio_client(params))

    def start(self) -> Self:
        """启动连接并等工具列表就绪；连接失败抛 ToolError。"""
        if self._thread is not None:
            return self
        self._thread = threading.Thread(target=self._run, name=f"mcp-{self.name}", daemon=True)
        self._thread.start()
        if not self._ready.wait(self.config.connect_timeout):
            raise ToolError(f"MCP server {self.name} 连接超时（{self.config.connect_timeout:g} 秒）")
        if self._error is not None:
            raise ToolError(f"MCP server {self.name} 连接失败: {self._error}")
        return self

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> str:
        """同步调用远程工具，返回给模型看的文本；失败抛 ToolError。"""
        client, loop = self._client, self._loop
        if client is None or loop is None:
            raise ToolError(f"MCP server {self.name} 未连接")
        future = asyncio.run_coroutine_threadsafe(self._invoke(client, name, dict(arguments)), loop)
        try:
            return future.result(self.config.call_timeout)
        except FutureTimeoutError as err:
            future.cancel()
            raise ToolError(f"MCP 工具 {name} 超时（{self.config.call_timeout:g} 秒）") from err

    def close(self) -> None:
        """通知后台线程退出并等待回收；可重复调用。"""
        loop, stop, thread = self._loop, self._stop, self._thread
        if loop is not None and stop is not None and not loop.is_closed():
            loop.call_soon_threadsafe(stop.set)
        if thread is not None:
            thread.join(timeout=5)
        self._thread = None
        self._loop = None
        self._stop = None
        self._client = None

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except Exception as err:  # 由 start() 转成 ToolError，交给调用方处理
            self._error = err
            self._ready.set()
        finally:
            loop.close()

    async def _serve(self) -> None:
        stop = asyncio.Event()  # 必须在自己的事件循环里创建
        self._stop = stop
        try:
            client = self._client_factory()
            async with client as connected:
                self._client = connected
                self.tools = await self._list_all_tools(connected)
                self._ready.set()
                await stop.wait()
        finally:
            self._client = None

    @staticmethod
    async def _list_all_tools(client: Client) -> list[mcp_types.Tool]:
        """按 cursor 翻完所有分页"""
        tools: list[mcp_types.Tool] = []
        cursor: str | None = None
        while True:
            page = await client.list_tools(cursor=cursor)
            tools.extend(page.tools)
            cursor = page.next_cursor
            if cursor is None:
                return tools

    @staticmethod
    async def _invoke(client: Client, name: str, arguments: dict[str, Any]) -> str:
        result = await client.call_tool(name, arguments)
        return render_result(name, result)


def render_result(name: str, result: mcp_types.CallToolResult) -> str:
    """把 MCP 的 content 块转成一段文本；错误结果抛 ToolError，消息原样交给模型。

    文本内容优先：多数 server 会同时给出给人和程序看的两种表示，结构化数据只在
    content 为空时兜底，避免同一份结果重复塞给模型。
    """
    text = "\n".join(text for block in result.content if (text := _render_block(block)))
    if not text and result.structured_content is not None:
        text = json.dumps(result.structured_content, ensure_ascii=False)
    if result.is_error:
        raise ToolError(text or f"MCP 工具 {name} 执行失败")
    return text or "（MCP 工具没有返回内容）"


def _render_block(block: mcp_types.ContentBlock) -> str:
    match block:
        case mcp_types.TextContent():
            return block.text
        case mcp_types.ImageContent():
            return f"[图片 {block.mime_type}，{len(block.data)} 个 base64 字符，未转成文本]"
        case mcp_types.AudioContent():
            return f"[音频 {block.mime_type}，未转成文本]"
        case mcp_types.ResourceLink():
            return f"[资源链接 {block.uri}]"
        case mcp_types.EmbeddedResource():
            resource = block.resource
            if isinstance(resource, mcp_types.TextResourceContents):
                return resource.text
            return f"[内嵌资源 {resource.uri}，二进制内容未转成文本]"
        case _:
            return block.model_dump_json()


class MCPTool(BaseTool):
    """远程 MCP 工具在本地的代理。

    名字加 ``mcp__{server}__`` 前缀，避免与本地工具重名；三项元数据来自运行期的
    ``tools/list``，所以按实例赋值（BaseTool 里声明为类属性）。
    """

    def __init__(self, connection: MCPConnection, remote: mcp_types.Tool) -> None:
        self.connection = connection
        self.remote_name = remote.name
        self.name = f"mcp__{connection.name}__{remote.name}"
        self.description = remote.description or f"{connection.name} 上的 MCP 工具 {remote.name}"
        self.parameters = remote.input_schema

    def run(self, **kwargs: Any) -> str:
        return self.connection.call_tool(self.remote_name, kwargs)


class MCPToolManager:
    """按配置启动多个 MCP server，把它们的工具汇总成 BaseTool 列表。"""

    def __init__(self, servers: Mapping[str, MCPServerConfig] | None = None) -> None:
        self._configs = dict(servers or {})
        self._connections: dict[str, MCPConnection] = {}
        self.errors: dict[str, str] = {}
        """启动失败的 server：名字 → 错误说明，由调用方决定是否展示"""

    @classmethod
    def from_file(cls, path: Path = DEFAULT_CONFIG_PATH) -> Self:
        """读取 ``{"mcpServers": {...}}``；文件不存在时返回空管理器，MCP 不参与对话。"""
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("mcpServers", {}) if isinstance(data, dict) else None
        if not isinstance(raw, dict):
            raise ValueError(f"{path} 缺少 mcpServers 对象")
        return cls({name: MCPServerConfig.model_validate(config) for name, config in raw.items()})

    def start(self) -> Self:
        """逐个连接；单个 server 失败只记进 errors，不影响其他 server。"""
        for name, config in self._configs.items():
            connection = MCPConnection(name, config)
            try:
                connection.start()
            except ToolError as err:
                self.errors[name] = str(err)
                print(f"[MCP] {err}", file=sys.stderr)
                continue
            self._connections[name] = connection
        return self

    def tools(self) -> list[MCPTool]:
        return [MCPTool(conn, remote) for conn in self._connections.values() for remote in conn.tools]

    def close(self) -> None:
        for connection in self._connections.values():
            connection.close()
        self._connections.clear()

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, *exc_info: object) -> None:
        self.close()
