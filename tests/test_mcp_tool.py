"""MCP 适配层单元测试（全部离线）。

运行方式（项目根目录）：
    python -m unittest tests.test_mcp_tool -v
"""

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from mcp import Client
from mcp import types as mcp_types
from mcp.server.mcpserver import MCPServer
from pydantic import ValidationError

from app.ai_tool import MCPServerConfig, ToolError, ToolRegistry
from app.ai_tool.mcp_tool import MCPConnection, MCPTool, MCPToolManager, render_result


def make_tool(name: str = "echo", schema: dict[str, Any] | None = None) -> mcp_types.Tool:
    return mcp_types.Tool(
        name=name,
        description=f"{name} 工具",
        input_schema=schema or {"type": "object", "properties": {}},
    )


def make_result(*blocks: mcp_types.ContentBlock, is_error: bool = False, structured: Any = None):
    return mcp_types.CallToolResult(content=list(blocks), is_error=is_error, structured_content=structured)


class FakeConnection:
    """假的 MCP 连接：记录调用参数并回显。"""

    def __init__(self, name: str = "demo") -> None:
        self.name = name
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        self.calls.append((name, arguments))
        return f"{name}:{json.dumps(arguments, ensure_ascii=False, sort_keys=True)}"


class ConfigTest(unittest.TestCase):
    def test_command_and_url_are_exclusive(self) -> None:
        with self.assertRaises(ValidationError):
            MCPServerConfig()
        with self.assertRaises(ValidationError):
            MCPServerConfig(command="x", url="http://localhost/mcp")

    def test_args_only_with_command(self) -> None:
        with self.assertRaises(ValidationError):
            MCPServerConfig(url="http://localhost/mcp", args=["--x"])

    def test_command_config(self) -> None:
        config = MCPServerConfig(command="npx", args=["-y", "server"], cwd="/tmp")
        self.assertEqual(config.command, "npx")
        self.assertEqual(config.args, ["-y", "server"])


class RenderTest(unittest.TestCase):
    def test_text_blocks_joined(self) -> None:
        result = make_result(mcp_types.TextContent(text="第一行"), mcp_types.TextContent(text="第二行"))
        self.assertEqual(render_result("demo", result), "第一行\n第二行")

    def test_structured_content_used_only_without_text(self) -> None:
        self.assertEqual(render_result("demo", make_result(structured={"count": 2})), '{"count": 2}')
        result = make_result(mcp_types.TextContent(text="ok"), structured={"count": 2})
        self.assertEqual(render_result("demo", result), "ok")

    def test_error_raises_tool_error(self) -> None:
        result = make_result(mcp_types.TextContent(text="参数不对"), is_error=True)
        with self.assertRaises(ToolError) as ctx:
            render_result("demo", result)
        self.assertEqual(str(ctx.exception), "参数不对")

    def test_empty_result(self) -> None:
        self.assertEqual(render_result("demo", make_result()), "（MCP 工具没有返回内容）")

    def test_non_text_blocks(self) -> None:
        result = make_result(
            mcp_types.ImageContent(data="aGk=", mime_type="image/png"),
            mcp_types.ResourceLink(uri="file:///tmp/a.txt", name="a.txt"),
            mcp_types.EmbeddedResource(
                resource=mcp_types.TextResourceContents(uri="file:///tmp/b.txt", text="内嵌正文")
            ),
        )
        text = render_result("demo", result)
        self.assertIn("image/png", text)
        self.assertIn("file:///tmp/a.txt", text)
        self.assertIn("内嵌正文", text)


class ToolTest(unittest.TestCase):
    def test_registry_routes_to_connection(self) -> None:
        connection = FakeConnection()
        tool = MCPTool(connection, make_tool("echo"))
        registry = ToolRegistry([tool])
        result = registry.execute("mcp__demo__echo", '{"text": "hi"}')
        self.assertEqual(result, 'echo:{"text": "hi"}')
        self.assertEqual(connection.calls, [("echo", {"text": "hi"})])

    def test_definition_prefixes_name(self) -> None:
        schema = {"type": "object", "properties": {"text": {"type": "string"}}}
        tool = MCPTool(FakeConnection(), make_tool("echo", schema))
        definition = tool.definition()
        self.assertEqual(definition["function"]["name"], "mcp__demo__echo")
        self.assertEqual(definition["function"]["description"], "echo 工具")
        self.assertEqual(definition["function"]["parameters"], schema)

    def test_unknown_name_reports(self) -> None:
        registry = ToolRegistry([MCPTool(FakeConnection(), make_tool())])
        self.assertEqual(registry.execute("nope", "{}"), "未知工具: nope")


class ManagerTest(unittest.TestCase):
    def test_missing_file_is_empty(self) -> None:
        manager = MCPToolManager.from_file(Path(tempfile.gettempdir()) / "不存在的-mcp.json")
        self.assertEqual(manager.tools(), [])

    def test_loads_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp_servers.json"
            path.write_text(
                json.dumps({"mcpServers": {"demo": {"command": "npx", "args": ["-y", "server"]}}}),
                encoding="utf-8",
            )
            manager = MCPToolManager.from_file(path)
        self.assertEqual(list(manager._configs), ["demo"])

    def test_bad_config_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp_servers.json"
            path.write_text(json.dumps({"mcpServers": {"demo": {}}}), encoding="utf-8")
            with self.assertRaises(ValidationError):
                MCPToolManager.from_file(path)


class InMemoryConnectionTest(unittest.TestCase):
    """用进程内 server 验证后台线程 + asyncio 桥接，不启动子进程、不联网。"""

    def setUp(self) -> None:
        server = MCPServer("demo")

        @server.tool()
        def add(a: int, b: int) -> int:
            """两数相加"""
            return a + b

        self.connection = MCPConnection(
            "demo",
            MCPServerConfig(command="unused"),
            client_factory=lambda: Client(server),
        )
        self.connection.start()
        self.addCleanup(self.connection.close)

    def test_lists_remote_tools(self) -> None:
        self.assertEqual([tool.name for tool in self.connection.tools], ["add"])

    def test_calls_remote_tool(self) -> None:
        self.assertEqual(self.connection.call_tool("add", {"a": 2, "b": 3}), "5")


if __name__ == "__main__":
    unittest.main()
