"""联网搜索工具：抓取 DuckDuckGo Lite 结果页作为实时信息来源。"""

import json
from html.parser import HTMLParser
from typing import Any, ClassVar

from app.ai_tool.base_tool import BaseTool
from app.ai_tool.net_client import NetClient


class _LiteResultParser(HTMLParser):
    """从 DuckDuckGo Lite 结果页抽出标题、链接和摘要。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._mode: str | None = None
        self._href = ""
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = attr.get("class", "").split()
        if tag == "a" and "result-link" in classes:
            self._flush()
            self._mode = "title"
            self._href = attr.get("href", "")
            self._parts = []
        elif tag == "td" and "result-snippet" in classes:
            self._flush()
            self._mode = "snippet"
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._mode == "title" and tag == "a":
            self._flush()
        elif self._mode == "snippet" and tag == "td":
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._mode is not None:
            self._parts.append(data)

    def _flush(self) -> None:
        text = " ".join("".join(self._parts).split())
        if self._mode == "title" and text:
            self.results.append({"title": text, "url": self._href, "snippet": ""})
        elif self._mode == "snippet" and text and self.results and not self.results[-1]["snippet"]:
            self.results[-1]["snippet"] = text
        self._mode = None
        self._href = ""
        self._parts = []


class WebSearchTool(BaseTool):
    """联网查询实时信息，并向对话模型提供函数定义。"""

    NAME = "web_search"
    DESCRIPTION = "联网搜索实时信息。用户询问新闻、最新事实或当前事件时调用，不要凭记忆编造。"
    PARAMETERS: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，例如「杭州今日新闻」",
            },
            "count": {
                "type": "integer",
                "description": "返回条数，1 到 8，默认 5",
            },
        },
        "required": ["query"],
    }

    def __init__(self, http: NetClient | None = None) -> None:
        """http 可注入假实现用于离线测试"""
        self.http = http or NetClient(timeout=15)

    def run(self, **kwargs: Any) -> str:
        query = kwargs.get("query")
        if not isinstance(query, str):
            return "缺少搜索词"
        count = kwargs.get("count", 5)
        return self.search(query, count if isinstance(count, int) else 5)

    def search(self, query: str, count: int = 5) -> str:
        """搜索网络结果；网络异常抛 ToolError"""
        query = query.strip()
        if not query:
            return "缺少搜索词"
        count = min(max(count, 1), 8)

        html = self.http.fetch_text(
            "https://lite.duckduckgo.com/lite/",
            {"q": query},
            headers={"Referer": "https://lite.duckduckgo.com/"},
        )

        parser = _LiteResultParser()
        parser.feed(html)
        rows = [row for row in parser.results if row["url"].startswith("http")][:count]
        if not rows:
            return f"没有找到与「{query}」相关的结果"
        return json.dumps({"query": query, "results": rows}, ensure_ascii=False)
