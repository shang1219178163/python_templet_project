"""把布局 CSS 送到 Streamlit 事件容器，避免占主栏位置、滚动时闪白。"""

from __future__ import annotations

import streamlit as st


def inject_css(css: str) -> None:
    st.html(f"<style>\n{css.strip()}\n</style>")
