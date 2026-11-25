"""路径规划工具：高德地图地理编码 + 驾车路线。"""

import json
from typing import Any

from app.ai_tool.tool_registry import BaseTool, NetClient, ToolError
from app.config import settings

GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
ROUTE_URL = "https://restapi.amap.com/v3/direction/driving"


class RoutePlannerTool(BaseTool):
    """用高德接口规划驾车路线，并向对话模型提供函数定义。"""

    name = "plan_route"
    description = "规划两地之间的驾车路线，返回距离、预计耗时和主要路段指引。用户询问怎么走、多远、开车多久时调用。"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "起点城市或地名，例如杭州、上海虹桥站",
            },
            "destination": {
                "type": "string",
                "description": "终点城市或地名，例如上海、北京天安门",
            },
        },
        "required": ["origin", "destination"],
    }

    MAX_STEPS = 12

    def __init__(self, http: NetClient | None = None, key: str | None = None) -> None:
        """http / key 可注入假实现用于离线测试；key 缺省读 .env 的 AMAP_KEY"""
        self.http = http or NetClient(timeout=15)
        self.key = settings.amap_key if key is None else key

    def run(self, **kwargs: Any) -> str:
        origin = kwargs.get("origin")
        destination = kwargs.get("destination")
        if not isinstance(origin, str) or not isinstance(destination, str):
            return "缺少起点或终点"
        return self.plan_route(origin, destination)

    def plan_route(self, origin: str, destination: str) -> str:
        """规划驾车路线；接口或网络异常抛 ToolError"""
        origin = origin.strip()
        destination = destination.strip()
        if not origin or not destination:
            return "缺少起点或终点"
        if not self.key:
            return "未配置高德地图密钥，请在 .env 中设置 AMAP_KEY"

        start = self._geocode(origin)
        if start is None:
            return f"没有找到地点: {origin}"
        end = self._geocode(destination)
        if end is None:
            return f"没有找到地点: {destination}"

        route = self.http.fetch_json(
            ROUTE_URL,
            {
                "key": self.key,
                "origin": start,
                "destination": end,
                "strategy": "0",
                "extensions": "base",
            },
        )
        if route.get("status") != "1":
            raise ToolError(f"高德路径规划失败: {route.get('info')}")
        paths = (route.get("route") or {}).get("paths") or []
        if not paths:
            return "未找到驾车路线"

        best = paths[0]
        steps = best.get("steps") or []
        payload: dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "distance_km": round(float(best.get("distance") or 0) / 1000, 1),
            "duration_min": round(float(best.get("duration") or 0) / 60),
            "steps": [
                {"instruction": step.get("instruction") or "", "distance_m": round(float(step.get("distance") or 0))}
                for step in steps[: self.MAX_STEPS]
            ],
        }
        if len(steps) > self.MAX_STEPS:
            payload["steps_truncated"] = len(steps) - self.MAX_STEPS
        return json.dumps(payload, ensure_ascii=False)

    def _geocode(self, name: str) -> str | None:
        """把地名解析成高德要求的 "经度,纬度"；找不到返回 None"""
        data = self.http.fetch_json(GEOCODE_URL, {"key": self.key, "address": name})
        if data.get("status") != "1":
            raise ToolError(f"高德地理编码失败: {data.get('info')}")
        geocodes = data.get("geocodes") or []
        location = str(geocodes[0].get("location") or "") if geocodes else ""
        return location or None
