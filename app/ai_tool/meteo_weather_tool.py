"""Open-Meteo 天气工具：免费、无需密钥的天气查询。"""

import json
from typing import Any, ClassVar

from app.ai_tool.tool_registry import BaseTool, NetClient


class MeteoWeatherTool(BaseTool):
    """查询 Open-Meteo，并向对话模型提供函数定义。"""

    name = "get_weather"
    description = "查询指定城市某一天的天气。用户询问气温、降雨、天气时调用，不要凭记忆编造。"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "城市名，例如杭州、北京、Shanghai",
            },
            "date": {
                "type": "string",
                "description": "日期，格式 YYYY-MM-DD。不传则查今天",
            },
        },
        "required": ["location"],
    }

    _WEATHER_TEXT: ClassVar[dict[int, str]] = {
        0: "晴",
        1: "大部晴朗",
        2: "多云",
        3: "阴",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "毛毛雨",
        55: "大毛毛雨",
        56: "冻毛毛雨",
        57: "强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "小阵雨",
        81: "阵雨",
        82: "强阵雨",
        85: "小阵雪",
        86: "大阵雪",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹",
    }

    def __init__(self, http: NetClient | None = None) -> None:
        """http 可注入假实现用于离线测试"""
        self.http = http or NetClient()

    def run(self, **kwargs: Any) -> str:
        location = kwargs.get("location")
        if not isinstance(location, str):
            return "缺少城市名"
        day = kwargs.get("date")
        return self.get_weather(location, day if isinstance(day, str) else None)

    def get_weather(self, location: str, day: str | None = None) -> str:
        """向 Open-Meteo 查询城市天气；网络或数据异常抛 ToolError"""
        location = location.strip()
        if not location:
            return "缺少城市名"

        geo = self.http.fetch_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": location, "count": "1", "language": "zh", "format": "json"},
        )
        results = geo.get("results") or []
        if not results:
            return f"没有找到城市: {location}"
        city = results[0]
        forecast = self.http.fetch_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": str(city["latitude"]),
                "longitude": str(city["longitude"]),
                "timezone": "auto",
                "current": "temperature_2m,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "forecast_days": "7",
            },
        )

        daily = forecast["daily"]
        days: list[str] = daily["time"]
        target = day or days[0]
        if target not in days:
            return f"{city['name']} 没有 {target} 的预报，可查范围 {days[0]} 到 {days[-1]}"

        index = days.index(target)
        payload: dict[str, object] = {
            "location": city["name"],
            "country": city.get("country", ""),
            "date": target,
            "condition": self._weather_text(daily["weather_code"][index]),
            "temp_min": daily["temperature_2m_min"][index],
            "temp_max": daily["temperature_2m_max"][index],
        }
        current = forecast.get("current")
        if target == days[0] and isinstance(current, dict):
            payload["current_temp"] = current.get("temperature_2m")
            payload["current_condition"] = self._weather_text(int(current.get("weather_code") or 0))
        return json.dumps(payload, ensure_ascii=False)

    def _weather_text(self, code: int) -> str:
        return self._WEATHER_TEXT.get(code, f"天气代码 {code}")
