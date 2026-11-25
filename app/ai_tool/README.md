# AI 工具模块

把外部能力（天气、搜索、路径规划、火车查询、图片 OCR 等）封装成模型可直接调用的函数工具，并提供统一的注册、声明与分发入口。

## 目录结构

```
app/ai_tool/
├── __init__.py               # 对外入口，导出 BaseTool / ToolError / ToolRegistry、内置工具与 MCP 适配层
├── tool_registry.py          # ToolError + BaseTool + NetClient + ToolRegistry
├── mcp_tool.py               # MCP 适配层：连接 MCP server，把远程工具注册进 ToolRegistry
├── meteo_weather_tool.py     # 天气工具：Open-Meteo
├── web_search_tool.py        # 搜索工具：DuckDuckGo Lite
├── route_planner_tool.py     # 路径规划工具：高德地图（需 AMAP_KEY）
├── train_tool.py             # 火车工具：12306 余票与经停站
├── ocr_tool.py               # 图片 OCR：ocrmac 优先，natocr 兜底
└── README.md
```

## 快速使用

```python
from app.ai_tool import (
    MCPToolManager,
    MeteoWeatherTool,
    OcrTool,
    RoutePlannerTool,
    ToolRegistry,
    TrainQueryTool,
    TrainStopsTool,
    WebSearchTool,
)

# MCP 可选：配置见 app/assets/mcp_servers.json，文件不存在时 manager.tools() 为空
manager = MCPToolManager.from_file().start()

registry = ToolRegistry([
    MeteoWeatherTool(),
    WebSearchTool(),
    RoutePlannerTool(),
    TrainQueryTool(),
    TrainStopsTool(),
    OcrTool(),
    *manager.tools(),
])

# 请求模型时带上函数定义
tools = registry.definitions()

# 收到 tool_calls 后按名字执行，永远返回 str
result = registry.execute("get_weather", '{"location": "杭州"}')
result = registry.execute(
    "query_train",
    '{"from_station": "北京南", "to_station": "上海虹桥", "date": "2026-11-27"}',
)
result = registry.execute(
    "query_train_stops",
    '{"from_station": "北京南", "to_station": "上海虹桥", "train_code": "G547", "date": "2026-11-27"}',
)
result = registry.execute("ocr_image", '{"image_path": "./data/screenshot.png"}')
```

完整对话循环见 `app/page/ai_chat_test.py`。

## 核心组成

| 名称 | 职责 |
| --- | --- |
| `BaseTool` | 工具基类：子类填 `name` / `description` / `parameters`，实现 `run(**kwargs) -> str`；`definition()` 生成 OpenAI 函数定义 |
| `ToolError` | 可预期的执行失败（网络异常、响应格式不对等），消息会原样交给模型 |
| `NetClient` | 共用 HTTP 客户端：统一 User-Agent 与超时（构造参数），每个实例维护 Cookie 会话，把网络异常收成 `ToolError`。定义在 `tool_registry.py`，不从包入口导出 |
| `ToolRegistry` | 注册工具、汇总函数定义、按名字分发，并兜住所有异常 |
| `MCPConnection` | 一个 MCP server 的连接：后台线程跑事件循环，对外是同步的 `start()` / `call_tool()` / `close()` |
| `MCPTool` | 远程 MCP 工具的本地代理，名字为 `mcp__{server}__{tool}`，注册后与本地工具同构 |
| `MCPToolManager` | 读配置、启动多个连接、汇总工具；单个 server 失败只记进 `errors` |

## 内置工具

| 工具类 | 调用名 | 参数 | 数据源 |
| --- | --- | --- | --- |
| `MeteoWeatherTool` | `get_weather` | `location`（必填）、`date`（`YYYY-MM-DD`，缺省为今天） | Open-Meteo，超时 10 秒，预报今天起 7 天 |
| `WebSearchTool` | `web_search` | `query`（必填）、`count`（1~8，默认 5） | DuckDuckGo Lite，超时 15 秒 |
| `RoutePlannerTool` | `plan_route` | `origin`、`destination`（均必填） | 高德地图地理编码 + 驾车路线，超时 15 秒，需配置 `AMAP_KEY` |
| `TrainQueryTool` | `query_train` | `from_station`、`to_station`（必填）、`date`（缺省今天）、`train_code`、`limit`（1~50，默认 20） | 12306 余票，超时 15 秒 |
| `TrainStopsTool` | `query_train_stops` | `from_station`、`to_station`、`train_code`（必填）、`date`（缺省今天） | 12306 经停站时刻，超时 15 秒 |
| `OcrTool` | `ocr_image` | `image_path`（必填，本地图片路径） | 本机 OCR：`ocrmac` 优先，`natocr` 兜底 |

成功时返回 JSON 字符串；没有数据或参数不全时返回中文说明文本。`plan_route` 返回 `distance_km`（千米，保留 1 位小数）和 `duration_min`（分钟，四舍五入取整）。`steps` 最多 12 段，每段含 `instruction` 与 `distance_m`，被省略的段数记在 `steps_truncated`。`query_train` 的 `trains` 按 `limit` 截断，被省略的车次数记在 `truncated`；`total` 是应用 `train_code` 过滤后、截断前的车次数。

### 天气查询说明

- 预报范围是今天起 7 天。日期超出范围时返回可查的起止日期。
- 查今天时额外返回 `current_temp`、`current_condition`；查其他日期只有 `location`、`country`、`date`、`condition`、`temp_min`、`temp_max`。
- 城市名找不到时返回「没有找到城市: xxx」，不再请求预报。

### 火车查询说明

- 车站要写到具体车站：查「北京南 → 上海虹桥」，而不是城市名「北京 → 上海」。末尾的「站」可以省略，「北京南站」与「北京南」等价。
- 站名对不上时，若有名称包含该关键字的车站，最多提示 5 个候选。
- 日期缺省为今天。支持 ISO 8601 日期（如 `2026-11-27`，也接受 `20261127` 等变体），无法解析时返回「日期格式应为 YYYY-MM-DD」；过去的日期直接拒绝。这两项都不访问网络。12306 通常只预售 15 天，超出预售期会查不到车次。
- `train_code` 不区分大小写。余票接口若返回区域查询地址，会自动再请求一次。
- 12306 要求先访问查询页取得会话 Cookie，`NetClient` 会自动保存并在后续请求中携带。
- `query_train` 每个车次包含 `train_code`、`from_station`、`to_station`、`start_time`、`arrive_time`、`duration`（历时原文）、`bookable` 和 `seats`。`seats` 是各席别余票：`有` 表示有票、`无` 表示售罄、数字表示剩余张数；该车次没有的席别不会出现。
- `query_train_stops` 需要区间车站来定位车次，返回全程经停站。每站包含 `station`、`arrive_time`、`start_time`、`stopover`。接口用 `----` 表示没有到发时刻或没有停站，统一收成空字符串。

### 图片 OCR 说明

- 只接受本机图片路径（图片、截图、扫描件均可），不处理网络 URL。路径中的 `~` 会展开；文件不存在时返回「找不到图片文件: ...」，不会调用识别引擎。
- 按 `ocrmac`、`natocr` 的顺序尝试。当前引擎未安装、抛异常，或没有识别到文字时，继续试下一个。
- `ocrmac` 走 Apple Vision，识别级别 `accurate`，语言偏好中文简体与英文。`natocr` 语言为 `auto`。
- 识别出文字时返回 JSON：`engine`（实际使用的引擎）、`image`（展开后的路径）、`text`（按行拼接）、`lines`（逐行列表）。
- 至少有一个引擎正常返回，但都没有文字时，返回「图片中没有识别到文字」。两个引擎都不可用时抛 `ToolError`，消息形如「OCR 识别失败: ...」。
- 依赖已写入 `pyproject.toml`：`ocrmac`、`natocr`，均为 macOS 原生 OCR 封装。

## MCP 工具

MCP（Model Context Protocol）server 上的工具会被自动登记为本地函数工具。适配层只做三件事：保持连接、把远程工具转成 OpenAI 函数定义、把调用结果转成文本。

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "remote_demo": {
      "url": "https://example.com/mcp"
    }
  }
}
```

- 配置文件：`app/assets/mcp_servers.json`，结构同 Claude Desktop 的 `mcpServers`。文件不存在或 `mcpServers` 为空时，MCP 不参与对话。
- `command` 与 `url` 必须且只能填一个：前者用 stdio 启动子进程，后者走 Streamable HTTP。
- `args`、`env`、`cwd` 只对 `command` 生效；`env` 在默认环境变量之上叠加。
- `connect_timeout`（默认 30 秒）约束启动握手；`call_timeout`（默认 60 秒）约束单次工具调用。
- 工具名统一加 `mcp__<server 名>__<远程工具名>` 前缀，避免与本地工具重名。
- 启动失败的 server 不影响其他 server，也不影响本地工具；错误记录在 `MCPToolManager.errors`，同时打到 stderr。
- 结果渲染：`content` 里的文本块按行拼接；图片、音频、资源链接只给说明；结构化数据仅在文本为空时使用，避免同一份结果重复塞给模型。`is_error` 的结果抛 `ToolError`，消息原样交给模型。

`MCPConnection` 的后台线程里跑 asyncio，所以同步的 CLI 代码不用改成 async。用完必须调用 `manager.close()`：它会通知线程退出，并等待 stdio 子进程收尾。

进程内用法（不启动子进程，测试或嵌入其他程序时用）：

```python
from mcp import Client

from app.ai_tool import MCPServerConfig
from app.ai_tool.mcp_tool import MCPConnection

connection = MCPConnection("demo", MCPServerConfig(command="unused"), client_factory=lambda: Client(server))
connection.start()
```

## 配置

路径规划工具需要高德「Web 服务」类型的 Key，在项目根目录 `.env` 中设置：

```
AMAP_KEY=你的高德Key
```

未配置时 `plan_route` 会返回提示文本，不影响其他工具。申请地址：<https://console.amap.com/dev/key/app>。

MCP server 的地址或启动命令写在 `app/assets/mcp_servers.json`，不放在 `.env` 里。

## 新增工具

```python
from typing import Any

from app.ai_tool import BaseTool
from app.ai_tool.tool_registry import NetClient


class IpLookupTool(BaseTool):
    name = "ip_lookup"
    description = "查询 IP 归属地。用户询问 IP 位置时调用。"
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {"ip": {"type": "string", "description": "要查询的 IP"}},
        "required": ["ip"],
    }

    def __init__(self, http: NetClient | None = None) -> None:
        self.http = http or NetClient()

    def run(self, **kwargs: Any) -> str:
        ip = kwargs.get("ip")
        if not isinstance(ip, str):
            return "缺少 IP"
        ...
```

然后注册：

```python
registry.register(IpLookupTool())
```

### 编写约定

1. 同一个 `ToolRegistry` 内 `name` 必须唯一，重名注册会抛 `ValueError`，避免模型调用被路由到错误实现。
2. `run()` 的参数来自模型，无法保证类型和完整性，**必须自行校验**。
3. 返回值是给模型看的文本，能结构化就返回 JSON 字符串。
4. 可预期的失败抛 `ToolError`；未预期的异常由 `ToolRegistry` 兜底成
   `工具 xxx 执行失败: ...`，不会中断对话。
5. 需要联网时复用 `NetClient`（从 `app.ai_tool.tool_registry` 导入，包入口不导出）。构造函数接收 `http: NetClient | None = None`，方便测试注入假实现。
6. 描述（`description`）里写清「什么时候调用」，直接影响模型是否选对工具。

## 错误处理约定

`ToolRegistry.execute()` 不向外抛异常，以下情况都返回中文文本。`arguments` 为空字符串时按 `{}` 解析，缺参由工具自己返回说明。

| 情况 | 返回 |
| --- | --- |
| 工具名不存在 | `未知工具: xxx` |
| 参数不是合法 JSON | `参数不是合法 JSON` |
| 参数不是 JSON 对象 | `参数必须是 JSON 对象` |
| 工具抛 `ToolError` | 异常消息原文 |
| 工具抛其他异常 | `工具 xxx 执行失败: ...` |

## 测试

先激活项目虚拟环境，再运行：

```bash
python -m unittest tests.test_ai_tool -v
python -m unittest tests.test_mcp_tool -v
```

测试全部离线：`FakeClient` 按顺序返回预置响应，不访问真实网络；MCP 测试用进程内 server，不启动子进程。
