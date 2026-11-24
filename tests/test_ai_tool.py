"""AI 工具模块单元测试（全部离线，不访问网络）。

运行方式（项目根目录）：
    python -m unittest tests.test_ai_tool -v
    python -m unittest discover -s tests -v
"""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.ai_tool import (
    BaseTool,
    MeteoWeatherTool,
    OcrTool,
    RoutePlannerTool,
    ToolError,
    ToolRegistry,
    TrainQueryTool,
    TrainStopsTool,
    WebSearchTool,
)
from app.ai_tool.train_tool import INIT_URL, QUERY_URL, STATION_URL, STOPS_URL


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
    name = "echo"
    description = "回显参数"
    parameters = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    def run(self, **kwargs: Any) -> str:
        return f"echo:{kwargs.get('text')}"


class BoomTool(BaseTool):
    name = "boom"
    description = "抛可预期异常"
    parameters = {"type": "object", "properties": {}}

    def run(self, **kwargs: Any) -> str:
        raise ToolError("可预期失败")


class CrashTool(BaseTool):
    name = "crash"
    description = "抛意外异常"
    parameters = {"type": "object", "properties": {}}

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

HANGZHOU_GEO = {"status": "1", "geocodes": [{"location": "120.153576,30.287459", "formatted_address": "浙江省杭州市"}]}

SHANGHAI_GEO = {"status": "1", "geocodes": [{"location": "121.473701,31.230416", "formatted_address": "上海市"}]}

ROUTE_RESPONSE = {
    "status": "1",
    "route": {
        "paths": [
            {
                "distance": "176500",
                "duration": "7500",
                "steps": [
                    {"instruction": "沿文三路向南行驶320米", "distance": "320"},
                    {"instruction": "右转进入学院路", "distance": "1500"},
                    {"instruction": "沿德胜快速路行驶", "distance": "5807"},
                ],
            }
        ]
    },
}


def make_weather_tool(*responses: Any) -> tuple[MeteoWeatherTool, FakeClient]:
    client = FakeClient(*responses)
    return MeteoWeatherTool(http=client), client


STATION_JS = (
    "var station_names ='@bjb|北京北|VAP|beijingbei|bjb|0|0357|北京|||"
    "@bji|北京|BJP|beijing|bj|2|0357|北京|||"
    "@vnp|北京南|VNP|beijingnan|bjn|3|0357|北京|||"
    "@shh|上海|SHH|shanghai|sh|2|0351|上海|||"
    "@aoh|上海虹桥|AOH|shanghaihongqiao|shhq|3|0351|上海|||"
    "@hzh|杭州|HZ|hangzhou|hz|4|0353|杭州|||"
    "@hgh|杭州东|HGH|hangzhoudong|hzd|5|0353|杭州|||';"
)

TRAIN_STATION_MAP = {
    "BJP": "北京",
    "VNP": "北京南",
    "SHH": "上海",
    "AOH": "上海虹桥",
    "HZ": "杭州",
    "HGH": "杭州东",
}


def make_ticket(
    code: str = "G547",
    train_no: str = "240000G54700",
    from_code: str = "VNP",
    to_code: str = "AOH",
    start: str = "06:18",
    arrive: str = "12:11",
    duration: str = "05:53",
    bookable: str = "Y",
    seats: dict[int, str] | None = None,
) -> str:
    """按 12306 余票行的下标布局拼一条数据"""
    fields = [""] * 58
    fields[0] = "secret"
    fields[2] = train_no
    fields[3] = code
    fields[6] = from_code
    fields[7] = to_code
    fields[8] = start
    fields[9] = arrive
    fields[10] = duration
    fields[11] = bookable
    seat_values = {26: "有", 30: "有", 31: "有", 32: "15"} if seats is None else seats
    for index, value in seat_values.items():
        fields[index] = value
    return "|".join(fields)


def left_tickets(*rows: str) -> dict[str, Any]:
    return {"status": True, "data": {"result": list(rows), "map": TRAIN_STATION_MAP}}


STOPS_RESPONSE = {
    "status": True,
    "data": {
        "data": [
            {
                "station_name": "北京南",
                "station_no": "01",
                "arrive_time": "----",
                "start_time": "06:18",
                "stopover_time": "----",
            },
            {
                "station_name": "沧州西",
                "station_no": "02",
                "arrive_time": "07:07",
                "start_time": "07:09",
                "stopover_time": "2分钟",
            },
            {
                "station_name": "上海虹桥",
                "station_no": "03",
                "arrive_time": "12:11",
                "start_time": "----",
                "stopover_time": "----",
            },
        ]
    },
}

FUTURE_DAY = (date.today() + timedelta(days=7)).isoformat()


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
        registry = ToolRegistry([
            MeteoWeatherTool(),
            WebSearchTool(),
            RoutePlannerTool(),
            TrainQueryTool(),
            TrainStopsTool(),
            OcrTool(),
        ])
        self.assertEqual(
            [item["function"]["name"] for item in registry.definitions()],
            ["get_weather", "web_search", "plan_route", "query_train", "query_train_stops", "ocr_image"],
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


class RoutePlannerToolTest(unittest.TestCase):
    def make_tool(self, *responses: Any) -> tuple[RoutePlannerTool, FakeClient]:
        client = FakeClient(*responses)
        return RoutePlannerTool(http=client, key="test-key"), client

    def test_plan_route_returns_distance_and_steps(self) -> None:
        tool, client = self.make_tool(HANGZHOU_GEO, SHANGHAI_GEO, ROUTE_RESPONSE)
        data = json.loads(tool.plan_route(" 杭州 ", "上海"))
        self.assertEqual(data["origin"], "杭州")
        self.assertEqual(data["destination"], "上海")
        self.assertEqual(data["distance_km"], 176.5)
        self.assertEqual(data["duration_min"], 125)
        self.assertEqual(
            [step["instruction"] for step in data["steps"]],
            ["沿文三路向南行驶320米", "右转进入学院路", "沿德胜快速路行驶"],
        )
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(client.calls[0][1]["address"], "杭州")
        self.assertEqual(client.calls[2][1]["origin"], "120.153576,30.287459")
        self.assertEqual(client.calls[2][1]["destination"], "121.473701,31.230416")
        self.assertTrue(all(call[1]["key"] == "test-key" for call in client.calls))

    def test_missing_key_does_not_hit_network(self) -> None:
        client = FakeClient()
        tool = RoutePlannerTool(http=client, key="")
        self.assertIn("AMAP_KEY", tool.plan_route("杭州", "上海"))
        self.assertEqual(client.calls, [])

    def test_origin_not_found(self) -> None:
        tool, client = self.make_tool({"status": "1", "geocodes": []})
        self.assertEqual(tool.plan_route("火星", "上海"), "没有找到地点: 火星")
        self.assertEqual(len(client.calls), 1)

    def test_destination_not_found(self) -> None:
        tool, _ = self.make_tool(HANGZHOU_GEO, {"status": "1", "geocodes": []})
        self.assertEqual(tool.plan_route("杭州", "火星"), "没有找到地点: 火星")

    def test_geocode_error_is_reported(self) -> None:
        tool, _ = self.make_tool({"status": "0", "info": "INVALID_USER_KEY"})
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute("plan_route", '{"origin": "杭州", "destination": "上海"}'),
            "高德地理编码失败: INVALID_USER_KEY",
        )

    def test_route_error_is_reported(self) -> None:
        tool, _ = self.make_tool(HANGZHOU_GEO, SHANGHAI_GEO, {"status": "0", "info": "DAILY_QUERY_OVER_LIMIT"})
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute("plan_route", '{"origin": "杭州", "destination": "上海"}'),
            "高德路径规划失败: DAILY_QUERY_OVER_LIMIT",
        )

    def test_no_route(self) -> None:
        tool, _ = self.make_tool(HANGZHOU_GEO, SHANGHAI_GEO, {"status": "1", "route": {"paths": []}})
        self.assertEqual(tool.plan_route("杭州", "上海"), "未找到驾车路线")

    def test_requires_both_endpoints(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.plan_route("杭州", "  "), "缺少起点或终点")
        self.assertEqual(tool.run(origin="杭州"), "缺少起点或终点")
        self.assertEqual(client.calls, [])

    def test_steps_are_truncated(self) -> None:
        steps = [{"instruction": "直行", "distance": "1"}] * 20
        response = {"status": "1", "route": {"paths": [{"distance": "1000", "duration": "60", "steps": steps}]}}
        tool, _ = self.make_tool(HANGZHOU_GEO, SHANGHAI_GEO, response)
        data = json.loads(tool.plan_route("杭州", "上海"))
        self.assertEqual(len(data["steps"]), 12)
        self.assertEqual(data["steps_truncated"], 8)

    def test_network_error_propagates_through_registry(self) -> None:
        tool, _ = self.make_tool(ToolError("网络请求失败: boom"))
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute("plan_route", '{"origin": "杭州", "destination": "上海"}'),
            "网络请求失败: boom",
        )


class TrainQueryToolTest(unittest.TestCase):
    def make_tool(self, *responses: Any) -> tuple[TrainQueryTool, FakeClient]:
        client = FakeClient(*responses)
        return TrainQueryTool(http=client), client

    def test_query_returns_trains_with_seats(self) -> None:
        rows = [
            make_ticket(),
            make_ticket(code="G1", train_no="24000000G10L", start="06:30", arrive="11:24", duration="04:54"),
        ]
        tool, client = self.make_tool(STATION_JS, "", left_tickets(*rows))
        data = json.loads(tool.query("北京南", "上海虹桥", FUTURE_DAY))
        self.assertEqual(data["date"], FUTURE_DAY)
        self.assertEqual(data["from_station"], "北京南")
        self.assertEqual(data["to_station"], "上海虹桥")
        self.assertEqual(data["total"], 2)
        first = data["trains"][0]
        self.assertEqual(first["train_code"], "G547")
        self.assertEqual(first["start_time"], "06:18")
        self.assertEqual(first["arrive_time"], "12:11")
        self.assertEqual(first["duration"], "05:53")
        self.assertTrue(first["bookable"])
        self.assertEqual(
            first["seats"],
            {"无座": "有", "二等座": "有", "一等座": "有", "商务座": "15"},
        )
        # 请求顺序：车站表 -> 初始化会话 -> 余票查询
        self.assertEqual([call[0] for call in client.calls], [STATION_URL, INIT_URL, QUERY_URL])
        self.assertEqual(
            client.calls[2][1],
            {
                "leftTicketDTO.train_date": FUTURE_DAY,
                "leftTicketDTO.from_station": "VNP",
                "leftTicketDTO.to_station": "AOH",
                "purpose_codes": "ADULT",
            },
        )

    def test_region_redirect_is_followed(self) -> None:
        tool, client = self.make_tool(
            STATION_JS,
            "",
            {"status": False, "c_url": "leftTicket/queryG"},
            left_tickets(make_ticket()),
        )
        data = json.loads(tool.query("北京南", "上海虹桥", FUTURE_DAY))
        self.assertEqual(data["total"], 1)
        self.assertEqual(client.calls[3][0], "https://kyfw.12306.cn/otn/leftTicket/queryG")
        self.assertEqual(client.calls[3][1], client.calls[2][1])

    def test_train_code_filter_ignores_case(self) -> None:
        rows = [make_ticket(), make_ticket(code="G1", train_no="24000000G10L")]
        tool, _ = self.make_tool(STATION_JS, "", left_tickets(*rows))
        data = json.loads(tool.query("北京南", "上海虹桥", FUTURE_DAY, train_code="g547"))
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["trains"][0]["train_code"], "G547")

    def test_train_code_without_match(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", left_tickets(make_ticket()))
        message = tool.query("北京南", "上海虹桥", FUTURE_DAY, train_code="G999")
        self.assertIn("没有找到车次 G999", message)

    def test_limit_truncates_results(self) -> None:
        rows = [make_ticket(code=f"G{i}", train_no=f"240000G{i}00") for i in range(1, 4)]
        tool, _ = self.make_tool(STATION_JS, "", left_tickets(*rows))
        data = json.loads(tool.query("北京南", "上海虹桥", FUTURE_DAY, limit=2))
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["trains"]), 2)
        self.assertEqual(data["truncated"], 1)

    def test_station_name_with_suffix(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", left_tickets(make_ticket()))
        data = json.loads(tool.query("北京南站", "上海虹桥站", FUTURE_DAY))
        self.assertEqual(data["from_station"], "北京南")
        self.assertEqual(data["to_station"], "上海虹桥")

    def test_unknown_station_lists_candidates(self) -> None:
        tool, client = self.make_tool(STATION_JS)
        message = tool.query("上海虹", "北京南", FUTURE_DAY)
        self.assertIn("没有找到车站「上海虹」", message)
        self.assertIn("上海虹桥", message)
        self.assertEqual(len(client.calls), 1)

    def test_past_date_rejected_without_network(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.query("北京南", "上海虹桥", "2000-01-01"), "不能查询过去的日期")
        self.assertEqual(client.calls, [])

    def test_bad_date_format(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.query("北京南", "上海虹桥", "2026/11/25"), "日期格式应为 YYYY-MM-DD")
        self.assertEqual(client.calls, [])

    def test_missing_stations(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.query("", "上海虹桥"), "缺少出发站或到达站")
        self.assertEqual(tool.run(from_station="北京南"), "缺少出发站或到达站")
        self.assertEqual(client.calls, [])

    def test_no_trains(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", left_tickets())
        self.assertIn("没有查到车次", tool.query("北京南", "上海虹桥", FUTURE_DAY))

    def test_run_passes_snake_case_arguments(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", left_tickets(make_ticket()))
        data = json.loads(
            tool.run(from_station="北京南", to_station="上海虹桥", date=FUTURE_DAY, limit=5)
        )
        self.assertEqual(data["total"], 1)

    def test_api_failure_through_registry(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", {"status": False, "messages": ["日期超出预售期"]})
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute("query_train", json.dumps({"from_station": "北京南", "to_station": "上海虹桥"})),
            "12306 查询失败: 日期超出预售期",
        )

    def test_malformed_payload_is_tool_error(self) -> None:
        tool, _ = self.make_tool(STATION_JS, "", {"status": True, "data": []})
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute("query_train", '{"from_station": "北京南", "to_station": "上海虹桥"}'),
            "12306 返回的数据格式异常",
        )


class TrainStopsToolTest(unittest.TestCase):
    def make_tool(self, *responses: Any) -> tuple[TrainStopsTool, FakeClient]:
        client = FakeClient(*responses)
        return TrainStopsTool(http=client), client

    def test_stops_returns_timetable(self) -> None:
        tool, client = self.make_tool(
            STATION_JS,
            "",
            left_tickets(make_ticket()),
            STOPS_RESPONSE,
        )
        data = json.loads(tool.query_stops("北京南", "上海虹桥", "g547", FUTURE_DAY))
        self.assertEqual(data["train_code"], "G547")
        self.assertEqual([stop["station"] for stop in data["stops"]], ["北京南", "沧州西", "上海虹桥"])
        self.assertEqual(data["stops"][0]["arrive_time"], "")
        self.assertEqual(data["stops"][0]["start_time"], "06:18")
        self.assertEqual(data["stops"][0]["stopover"], "")
        self.assertEqual(data["stops"][1]["stopover"], "2分钟")
        self.assertEqual(data["stops"][2]["start_time"], "")
        self.assertEqual(client.calls[3][0], STOPS_URL)
        self.assertEqual(
            client.calls[3][1],
            {
                "train_no": "240000G54700",
                "from_station_telecode": "VNP",
                "to_station_telecode": "AOH",
                "depart_date": FUTURE_DAY,
            },
        )

    def test_train_not_found(self) -> None:
        tool, client = self.make_tool(
            STATION_JS,
            "",
            left_tickets(make_ticket(code="G1", train_no="24000000G10L")),
        )
        message = tool.query_stops("北京南", "上海虹桥", "G547", FUTURE_DAY)
        self.assertIn("没有找到车次 G547", message)
        self.assertEqual(len(client.calls), 3)

    def test_missing_train_code_does_not_hit_network(self) -> None:
        tool, client = self.make_tool()
        self.assertEqual(tool.query_stops("北京南", "上海虹桥", "  "), "缺少车次")
        self.assertEqual(tool.run(from_station="北京南", to_station="上海虹桥"), "缺少出发站、到达站或车次")
        self.assertEqual(client.calls, [])

    def test_stops_request_failure(self) -> None:
        tool, _ = self.make_tool(
            STATION_JS,
            "",
            left_tickets(make_ticket()),
            {"status": False, "messages": ["车次不存在"]},
        )
        registry = ToolRegistry([tool])
        self.assertEqual(
            registry.execute(
                "query_train_stops",
                json.dumps({"from_station": "北京南", "to_station": "上海虹桥", "train_code": "G547"}),
            ),
            "12306 车次时刻查询失败: 车次不存在",
        )


class OcrToolTest(unittest.TestCase):
    def setUp(self) -> None:
        handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        handle.close()
        self.image = handle.name
        self.addCleanup(Path(self.image).unlink, missing_ok=True)

    def test_ocrmac_is_preferred(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", return_value=["你好，世界！", " OCR Test "]),
            patch.object(OcrTool, "_recognize_natocr") as fallback,
        ):
            data = json.loads(tool.recognize(self.image))
        self.assertEqual(data["engine"], "ocrmac")
        self.assertEqual(data["text"], "你好，世界！\nOCR Test")
        self.assertEqual(data["lines"], ["你好，世界！", "OCR Test"])
        fallback.assert_not_called()

    def test_falls_back_when_ocrmac_raises(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", side_effect=RuntimeError("Vision 不可用")),
            patch.object(OcrTool, "_recognize_natocr", return_value=["备用结果"]),
        ):
            data = json.loads(tool.recognize(self.image))
        self.assertEqual(data["engine"], "natocr")
        self.assertEqual(data["text"], "备用结果")

    def test_falls_back_when_ocrmac_missing(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", side_effect=ImportError("No module named 'ocrmac'")),
            patch.object(OcrTool, "_recognize_natocr", return_value=["备用结果"]),
        ):
            self.assertEqual(json.loads(tool.recognize(self.image))["engine"], "natocr")

    def test_empty_ocrmac_result_falls_back(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", return_value=["   "]),
            patch.object(OcrTool, "_recognize_natocr", return_value=["有文字"]),
        ):
            data = json.loads(tool.recognize(self.image))
        self.assertEqual(data["engine"], "natocr")
        self.assertEqual(data["text"], "有文字")

    def test_both_engines_empty(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", return_value=[]),
            patch.object(OcrTool, "_recognize_natocr", return_value=[]),
        ):
            self.assertEqual(tool.recognize(self.image), "图片中没有识别到文字")

    def test_both_engines_unavailable(self) -> None:
        tool = OcrTool()
        with (
            patch.object(OcrTool, "_recognize_ocrmac", side_effect=ImportError("No module named 'ocrmac'")),
            patch.object(OcrTool, "_recognize_natocr", side_effect=ImportError("No module named 'natocr'")),
        ):
            registry = ToolRegistry([tool])
            message = registry.execute("ocr_image", json.dumps({"image_path": self.image}))
        self.assertIn("OCR 识别失败", message)
        self.assertIn("ocrmac 未安装", message)
        self.assertIn("natocr 未安装", message)

    def test_missing_file_does_not_call_engines(self) -> None:
        tool = OcrTool()
        with patch.object(OcrTool, "_recognize_ocrmac") as engine:
            message = tool.recognize("/tmp/not-exists-ocr-test.png")
        self.assertIn("找不到图片文件", message)
        engine.assert_not_called()

    def test_requires_image_path(self) -> None:
        tool = OcrTool()
        self.assertEqual(tool.run(), "缺少图片路径")
        self.assertEqual(tool.run(image_path="  "), "缺少图片路径")


if __name__ == "__main__":
    unittest.main()
