"""AI 工具模块：把外部能力封装成模型可调用的函数工具。

典型用法：
    registry = ToolRegistry([MeteoWeatherTool(), WebSearchTool()])
    # 请求模型时带上 registry.definitions()
    # 收到 tool_calls 后逐个执行 registry.execute(name, arguments)
"""

from app.ai_tool.meteo_weather_tool import MeteoWeatherTool
from app.ai_tool.tool_registry import BaseTool, ToolError, ToolRegistry
from app.ai_tool.web_search_tool import WebSearchTool

__all__ = ["BaseTool", "ToolError", "ToolRegistry", "MeteoWeatherTool", "WebSearchTool"]
