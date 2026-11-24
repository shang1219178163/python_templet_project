"""中国铁路 12306 查询工具：车站解析、余票车次与经停站时刻。"""

import json
from datetime import date
from typing import Any, ClassVar, NamedTuple

from app.ai_tool.tool_registry import BaseTool, NetClient, ToolError

BASE_URL = "https://kyfw.12306.cn/otn"
INIT_URL = f"{BASE_URL}/leftTicket/init?linktypeid=dc"
QUERY_URL = f"{BASE_URL}/leftTicket/query"
STATION_URL = f"{BASE_URL}/resources/js/framework/station_name.js"
STOPS_URL = f"{BASE_URL}/czxx/queryByTrainNo"

# 12306 余票行（| 分隔）中席别所在的下标
SEAT_FIELDS: tuple[tuple[int, str], ...] = (
    (21, "高级软卧"),
    (23, "软卧"),
    (24, "软座"),
    (26, "无座"),
    (28, "硬卧"),
    (29, "硬座"),
    (30, "二等座"),
    (31, "一等座"),
    (32, "商务座"),
    (33, "动卧"),
)


class _Station(NamedTuple):
    name: str
    code: str


def _parse_ticket(row: str, station_map: dict[str, Any]) -> dict[str, Any] | None:
    """把一条余票字符串解析成车次信息；格式不符返回 None"""
    fields = row.split("|")
    if len(fields) < 34 or not fields[3]:
        return None
    seats = {
        name: fields[index]
        for index, name in SEAT_FIELDS
        if fields[index] and fields[index] != "*"
    }
    return {
        "train_code": fields[3],
        "from_station": station_map.get(fields[6]) or fields[6],
        "to_station": station_map.get(fields[7]) or fields[7],
        "start_time": fields[8],
        "arrive_time": fields[9],
        "duration": fields[10],
        "bookable": fields[11] == "Y",
        "seats": seats,
    }


class _TrainToolBase(BaseTool):
    """12306 工具共用部分：会话初始化、车站解析、余票列表。"""

    def __init__(self, http: NetClient | None = None) -> None:
        """http 可注入假实现用于离线测试"""
        self.http = http or NetClient(timeout=15)
        self._stations: dict[str, _Station] | None = None
        self._session_ready = False

    def _parse_request(
        self,
        origin: str,
        target: str,
        day: str | None,
    ) -> tuple[str, _Station, _Station] | str:
        """校验起终站与日期；失败时返回给模型的提示文本"""
        origin, target = origin.strip(), target.strip()
        if not origin or not target:
            return "缺少出发站或到达站"

        normalized = self._normalize_day(day)
        if normalized is None:
            return "日期格式应为 YYYY-MM-DD"
        if normalized < date.today().isoformat():
            return "不能查询过去的日期"

        start = self._find_station(origin)
        if start is None:
            return self._unknown_station(origin)
        end = self._find_station(target)
        if end is None:
            return self._unknown_station(target)
        return normalized, start, end

    def _normalize_day(self, raw: str | None) -> str | None:
        """缺省为今天；格式非法返回 None"""
        if raw is None or not raw.strip():
            return date.today().isoformat()
        try:
            return date.fromisoformat(raw.strip()).isoformat()
        except ValueError:
            return None

    def _find_station(self, raw: str) -> _Station | None:
        return self._load_stations().get(self._station_key(raw))

    def _unknown_station(self, raw: str) -> str:
        key = self._station_key(raw)
        candidates = sorted(
            {station.name for station in self._load_stations().values() if key and key in station.name}
        )
        if candidates:
            return f"没有找到车站「{raw}」，你可能想查: {'、'.join(candidates[:5])}"
        return f"没有找到车站: {raw}"

    @staticmethod
    def _station_key(raw: str) -> str:
        """统一「北京南」「北京南站」两种写法"""
        name = raw.strip()
        return name[:-1] if name.endswith("站") and len(name) > 1 else name

    def _load_stations(self) -> dict[str, _Station]:
        """解析 station_name.js，缓存「站名 -> (标准名, 电报码)」"""
        if self._stations is not None:
            return self._stations
        text = self.http.fetch_text(STATION_URL)
        stations: dict[str, _Station] = {}
        for entry in text.split("@"):
            fields = entry.split("|")
            if len(fields) < 8 or not fields[1] or not fields[2]:
                continue
            station = _Station(fields[1], fields[2])
            stations[station.name] = station
            stations[f"{station.name}站"] = station
        if not stations:
            raise ToolError("12306 车站列表解析失败")
        self._stations = stations
        return stations

    def _ensure_session(self) -> None:
        """先访问查询页取会话 Cookie，否则余票接口会跳到错误页"""
        if not self._session_ready:
            self.http.fetch_text(INIT_URL)
            self._session_ready = True

    def _left_tickets(self, start: _Station, end: _Station, day: str) -> dict[str, Any]:
        """查询余票原始数据；接口或数据异常抛 ToolError"""
        self._ensure_session()
        params = {
            "leftTicketDTO.train_date": day,
            "leftTicketDTO.from_station": start.code,
            "leftTicketDTO.to_station": end.code,
            "purpose_codes": "ADULT",
        }
        data = self.http.fetch_json(QUERY_URL, params)
        # 12306 会按区域返回查询接口名（如 leftTicket/queryG），跟着跳一次
        redirect = data.get("c_url")
        if isinstance(redirect, str) and redirect.startswith("leftTicket/"):
            data = self.http.fetch_json(f"{BASE_URL}/{redirect}", params)
        if not self._is_ok(data):
            raise ToolError(f"12306 查询失败: {self._detail(data)}")
        payload = data.get("data")
        if not isinstance(payload, dict):
            raise ToolError("12306 返回的数据格式异常")
        return payload

    @staticmethod
    def _is_ok(data: dict[str, Any]) -> bool:
        return data.get("status") is True or data.get("status") in ("1", 1)

    @staticmethod
    def _detail(data: dict[str, Any]) -> str:
        messages = data.get("messages")
        if isinstance(messages, list) and messages:
            return "；".join(str(item) for item in messages)
        return str(messages or "未知原因")


class TrainQueryTool(_TrainToolBase):
    """查询余票与车次时刻，并向对话模型提供函数定义。"""

    name = "query_train"
    description = (
        "查询中国铁路某天两个车站之间的车次、发到时刻、历时和余票。"
        "用户询问火车票、车次、几点发车、有没有票时调用，不要凭记忆编造。"
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "from_station": {
                "type": "string",
                "description": "出发车站，例如北京南、上海虹桥、杭州东",
            },
            "to_station": {
                "type": "string",
                "description": "到达车站，例如北京南、上海虹桥、杭州东",
            },
            "date": {
                "type": "string",
                "description": "乘车日期，格式 YYYY-MM-DD。不传则查今天",
            },
            "train_code": {
                "type": "string",
                "description": "只看某个车次时传入，例如 G547",
            },
            "limit": {
                "type": "integer",
                "description": "最多返回多少个车次，1 到 50，默认 20",
            },
        },
        "required": ["from_station", "to_station"],
    }

    def run(self, **kwargs: Any) -> str:
        origin = kwargs.get("from_station")
        target = kwargs.get("to_station")
        if not isinstance(origin, str) or not isinstance(target, str):
            return "缺少出发站或到达站"
        day = kwargs.get("date")
        code = kwargs.get("train_code")
        limit = kwargs.get("limit")
        return self.query(
            origin,
            target,
            day if isinstance(day, str) else None,
            train_code=code if isinstance(code, str) else None,
            limit=limit if isinstance(limit, int) else 20,
        )

    def query(
        self,
        origin: str,
        target: str,
        day: str | None = None,
        *,
        train_code: str | None = None,
        limit: int = 20,
    ) -> str:
        """查询余票；参数问题返回说明文本，接口异常抛 ToolError"""
        prepared = self._parse_request(origin, target, day)
        if isinstance(prepared, str):
            return prepared
        day, start, end = prepared

        payload = self._left_tickets(start, end, day)
        station_map = payload.get("map") or {}
        wanted = train_code.strip().upper() if train_code else None

        trains: list[dict[str, Any]] = []
        for row in payload.get("result") or []:
            ticket = _parse_ticket(row, station_map) if isinstance(row, str) else None
            if ticket is None:
                continue
            if wanted and ticket["train_code"].upper() != wanted:
                continue
            trains.append(ticket)

        if not trains:
            hint = f"，没有找到车次 {wanted}" if wanted else ""
            return (
                f"{day} {start.name} 到 {end.name} 没有查到车次{hint}，"
                "请确认车站和日期（12306 通常只预售 15 天内车票）"
            )

        limit = min(max(limit, 1), 50)
        result: dict[str, Any] = {
            "date": day,
            "from_station": start.name,
            "to_station": end.name,
            "total": len(trains),
            "trains": trains[:limit],
        }
        if len(trains) > limit:
            result["truncated"] = len(trains) - limit
        return json.dumps(result, ensure_ascii=False)


class TrainStopsTool(_TrainToolBase):
    """查询指定车次的全程经停站与到发时刻。"""

    name = "query_train_stops"
    description = (
        "查询某趟中国铁路列车沿途经停哪些站、各站几点到几点开。"
        "用户询问车次时刻表、经停站时调用，需要同时给出区间车站和车次。"
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "from_station": {
                "type": "string",
                "description": "车次区间内的出发车站，例如北京南",
            },
            "to_station": {
                "type": "string",
                "description": "车次区间内的到达车站，例如上海虹桥",
            },
            "train_code": {
                "type": "string",
                "description": "要查询的车次，例如 G547",
            },
            "date": {
                "type": "string",
                "description": "乘车日期，格式 YYYY-MM-DD。不传则查今天",
            },
        },
        "required": ["from_station", "to_station", "train_code"],
    }

    def run(self, **kwargs: Any) -> str:
        origin = kwargs.get("from_station")
        target = kwargs.get("to_station")
        code = kwargs.get("train_code")
        if not isinstance(origin, str) or not isinstance(target, str) or not isinstance(code, str):
            return "缺少出发站、到达站或车次"
        day = kwargs.get("date")
        return self.query_stops(origin, target, code, day if isinstance(day, str) else None)

    def query_stops(
        self,
        origin: str,
        target: str,
        train_code: str,
        day: str | None = None,
    ) -> str:
        """查询车次经停站；参数问题返回说明文本，接口异常抛 ToolError"""
        wanted = train_code.strip().upper()
        if not wanted:
            return "缺少车次"

        prepared = self._parse_request(origin, target, day)
        if isinstance(prepared, str):
            return prepared
        day, start, end = prepared

        payload = self._left_tickets(start, end, day)
        station_map = payload.get("map") or {}
        fields: list[str] | None = None
        for row in payload.get("result") or []:
            ticket = _parse_ticket(row, station_map) if isinstance(row, str) else None
            if ticket is not None and ticket["train_code"].upper() == wanted:
                fields = row.split("|")
                break
        if fields is None:
            return f"{day} {start.name} 到 {end.name} 没有找到车次 {wanted}"

        stops = self._fetch_stops(fields, day)
        result = {
            "train_code": fields[3],
            "date": day,
            "from_station": start.name,
            "to_station": end.name,
            "stops": stops,
        }
        return json.dumps(result, ensure_ascii=False)

    def _fetch_stops(self, fields: list[str], day: str) -> list[dict[str, str]]:
        data = self.http.fetch_json(
            STOPS_URL,
            {
                "train_no": fields[2],
                "from_station_telecode": fields[6],
                "to_station_telecode": fields[7],
                "depart_date": day,
            },
        )
        if not self._is_ok(data):
            raise ToolError(f"12306 车次时刻查询失败: {self._detail(data)}")
        payload = data.get("data")
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ToolError("12306 车次时刻数据格式异常")
        return [
            {
                "station": item.get("station_name") or "",
                "arrive_time": self._time(item.get("arrive_time")),
                "start_time": self._time(item.get("start_time")),
                "stopover": self._time(item.get("stopover_time")),
            }
            for item in rows
            if isinstance(item, dict)
        ]

    @staticmethod
    def _time(value: Any) -> str:
        """接口用 ---- 表示无到发时刻或无停站，统一成空串"""
        return value if isinstance(value, str) and value != "----" else ""
