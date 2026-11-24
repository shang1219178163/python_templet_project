"""AI 工具模块单元测试（全部离线，不访问网络）。

运行方式（项目根目录）：
    python -m unittest tests.test_ai_tool -v
    python -m unittest discover -s tests -v
"""

import json
import unittest
from typing import Any

from app.ai_tool import BaseTool, MeteoWeatherTool, ToolError, ToolRegistry, WebSearchTool


class FakeClient:
    """假的网络客户端：按顺序返回预置响应，并记录收到的请求。"""

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, str]]] = []

    def fetch_json(self, url: str, params: dict[str, str]) -> Any:
        self.calls.append((url, params))
        return self._next()

    def fetch_text(self, url: str, form: Any = None, *, headers: Any = None) -> str:
        self.calls.append((url, dict(form or {})))
        return self._next()

    def _next(self) -> Any:
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class EchoTool(BaseTool):
    NAME = "echo"
    DESCRIPTION = "回显参数"
    PARAMETERS = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    def run(self, **kwargs: Any) -> str:
        return f"echo:{kwargs.get('text')}"


class BoomTool(BaseTool):
    NAME = "boom"
    DESCRIPTION = "抛可预期异常"
    PARAMETERS = {"type": "object", "properties": {}}

    def run(self, **kwargs: Any) -> str:
        raise ToolError("可预期失败")


class CrashTool(BaseTool):
    NAME = "crash"
    DESCRIPTION = "抛意外异常"
    PARAMETERS = {"type": "object", "properties": {}}

    def run(self, **kwargs: Any) -> str:
        raise RuntimeError("意外失败")


GEO_RESPONSE = {"results": [{"name": "杭州", "country": "中国", "latitude": 30.29, "longitude": 120.16}]}

FORECAST_RESPONSE = {
    "daily": {
        "time": ["2026-11-24", "2026-11-25"],
        "weather_code": [0, 3],
        "temperature_2m_min": [4.7, 6.1],
        "temperature_2m_max": [13.0, 14.2],
    },
    "current": {"temperature_2m": 12.0, "weather_code": 1},
}

SEARCH_HTML = """
<table>
  <tr><td><a class="result-link" href="https://example.com/a">标题一</a></td></tr>
  <tr><td class="result-snippet">摘要一</td></tr>
  <tr><td><a class="result-link" href="https://example.com/b">标题二</a></td></tr>
  <tr><td class="result-snippet">摘要二</td></tr>
</table>
"""


def make_weather_tool(*responses: Any) -> tuple[MeteoWeatherTool, FakeClient]:
    client = FakeClient(*responses)
    return MeteoWeatherTool(http=client), client


class ToolRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ToolRegistry([EchoTool(), BoomTool(), CrashTool()])

    def test_definitions_follow_openai_schema(self) -> None:
        definitions = self.registry.definitions()
        self.assertEqual([item["function"]["name"] for item in definitions], ["echo", "boom", "crash"])
        self.assertEqual(definitions[0]["type"], "function")

    def test_execute_dispatches_by_name(self) -> None:
        self.assertEqual(self.registry.execute("echo", '{"text": "hi"}'), "echo:hi")

    def test_empty_arguments_are_treated_as_empty_object(self) -> None:
        self.assertEqual(self.registry.execute("echo", ""), "echo:None")

    def test_invalid_json(self) -> None:
        self.assertEqual(self.registry.execute("echo", "{oops"), "参数不是合法 JSON")

    def test_non_object_json(self) -> None:
        self.assertEqual(self.registry.execute("echo", "[1, 2]"), "参数必须是 JSON 对象")

    def test_unknown_tool(self) -> None:
        self.assertEqual(self.registry.execute("nope", "{}"), "未知工具: nope")

    def test_tool_error_message_is_passed_through(self) -> None:
        self.assertEqual(self.registry.execute("boom", "{}"), "可预期失败")

    def test_unexpected_error_is_contained(self) -> None:
        self.assertEqual(self.registry.execute("crash", "{}"), "工具 crash 执行失败: 意外失败")

    def test_duplicate_name_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.registry.register(EchoTool())

    def test_real_tools_register(self) -> None:
        registry = ToolRegistry([MeteoWeatherTool(), WebSearchTool()])
        self.assertEqual(
            [item["function"]["name"] for item in registry.definitions()],
            ["get_weather", "web_search"],
        )


class MeteoWeatherToolTest(unittest.TestCase):
    def test_today_returns_current_weather(self) -> None:
        tool, client = make_weather_tool(GEO_RESPONSE, FORECAST_RESPONSE)
        data = json.loads(tool.get_weather(" 杭州 "))
        self.assertEqual(data["location"], "杭州")
        self.assertEqual(data["date"], "2026-11-24")
        self.assertEqual(data["condition"], "晴")
        self.assertEqual(data["temp_min"], 4.7)
        self.assertEqual(data["temp_max"], 13.0)
        self.assertEqual(data["current_temp"], 12.0)
        self.assertEqual(data["current_condition"], "大部晴朗")
        self.assertEqual(len(client.calls), 2)

    def test_specific_day_has_no_current_block(self) -> None:
        tool, _ = make_weather_tool(GEO_RESPONSE, FORECAST_RESPONSE)
        data = json.loads(tool.get_weather("杭州", "2026-11-25"))
        self.assertEqual(data["condition"], "阴")
        self.assertNotIn("current_temp", data)

    def test_day_out_of_range_lists_available_days(self) -> None:
        tool, _ = make_weather_tool(GEO_RESPONSE, FORECAST_RESPONSE)
        message = tool.get_weather("杭州", "1999-01-01")
        self.assertIn("没有 1999-01-01 的预报", message)
        self.assertIn("2026-11-24 到 2026-11-25", message)

    def test_unknown_city(self) -> None:
        tool, _ = make_weather_tool({"results": []})
        self.assertEqual(tool.get_weather("不存在"), "没有找到城市: 不存在")

    def test_blank_location_does_not_hit_network(self) -> None:
        tool, client = make_weather_tool()
        self.assertEqual(tool.get_weather("   "), "缺少城市名")
        self.assertEqual(client.calls, [])

    def test_network_error_becomes_tool_error(self) -> None:
        tool, _ = make_weather_tool(ToolError("网络请求失败: boom"))
        with self.assertRaises(ToolError):
            tool.get_weather("杭州")

    def test_registry_returns_error_text(self) -> None:
        tool, _ = make_weather_tool(ToolError("网络请求失败: boom"))
        registry = ToolRegistry([tool])
        self.assertEqual(registry.execute("get_weather", '{"location": "杭州"}'), "网络请求失败: boom")


class WebSearchToolTest(unittest.TestCase):
    def make_tool(self, *responses: Any) -> tuple[WebSearchTool, FakeClient]:
        client = FakeClient(*responses)
        return WebSearchTool(http=client), client

    def test_search_parses_results(self) -> None:
        tool, client = self.make_tool(SEARCH_HTML)
        data = json.loads(tool.search("杭州 新闻"))
        self.assertEqual(data["query"], "杭州 新闻")
        self.assertEqual([row["title"] for row in data["results"]], ["标题一", "标题二"])
        self.assertEqual(data["results"][0]["url"], "https://example.com/a")
        self.assertEqual(data["results"][0]["snippet"], "摘要一")
        self.assertEqual(client.calls[0][1], {"q": "杭州 新闻"})

    def test_count_limit_and_clamp(self) -> None:
        tool, _ = self.make_tool(SEARCH_HTML)
        self.assertEqual(len(json.loads(tool.search("x", 1))["results"]), 1)
        tool, _ = self.make_tool(SEARCH_HTML)
        self.assertEqual(len(json.loads(tool.search("x", 999))["results"]), 2)

    def test_no_results(self) -> None:
        tool, _ = self.make_tool("<html></html>")
        self.assertEqual(tool.search("x"), "没有找到与「x」相关的结果")

    def test_blank_query_does_not_hit_network(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.search("  "), "缺少搜索词")
        self.assertEqual(client.calls, [])

    def test_run_requires_query(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.run(), "缺少搜索词")
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
