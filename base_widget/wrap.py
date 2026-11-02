"""Flutter Wrap 的 Streamlit 封装。

子组件沿主轴排列，空间不够时换到下一行（或下一列）。
"""

from __future__ import annotations

from types import TracebackType

import streamlit as st

from base_widget._layout import css_px, gap_token, streamlit_cross_align, streamlit_main_align
from base_widget.axis import Axis


class WrapAlignment:
    start = "start"
    end = "end"
    center = "center"
    space_between = "space_between"
    space_around = "space_around"
    space_evenly = "space_evenly"


class WrapCrossAlignment:
    start = "start"
    end = "end"
    center = "center"


class Wrap:
    """流水布局，对齐 Flutter ``Wrap``。

    用法::

        with Wrap(spacing=8, run_spacing=8):
            st.button("按钮1")
            st.button("按钮2")
    """

    def __init__(
        self,
        *,
        direction: str = Axis.horizontal,
        alignment: str = WrapAlignment.start,
        spacing: float | str = 8,
        run_spacing: float | str | None = None,
        run_alignment: str = WrapAlignment.start,
        cross_axis_alignment: str = WrapCrossAlignment.start,
        key: str | None = None,
    ) -> None:
        self.direction = direction
        self.alignment = alignment
        self.spacing = spacing
        self.run_spacing = spacing if run_spacing is None else run_spacing
        self.run_alignment = run_alignment
        self.cross_axis_alignment = cross_axis_alignment
        self.key = key
        self._container = None

    def __enter__(self):
        horizontal = self.direction == Axis.horizontal
        main_align = streamlit_main_align(self.alignment, horizontal=horizontal)
        cross_align = streamlit_cross_align(self.cross_axis_alignment, horizontal=horizontal)
        if not horizontal:
            main_align = streamlit_main_align(self.run_alignment, horizontal=horizontal)

        gap = gap_token(self.spacing)
        wrap_key = self.key or f"flutter_wrap_{id(self)}"
        self._inject_css(wrap_key)
        self._container = st.container(
            key=wrap_key,
            horizontal=horizontal,
            wrap=True,
            gap=gap,
            horizontal_alignment=main_align if horizontal else cross_align,
            vertical_alignment=cross_align if horizontal else main_align,
        )
        return self._container.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        if self._container is None:
            return None
        return self._container.__exit__(exc_type, exc, tb)

    def _inject_css(self, wrap_key: str) -> None:
        spacing = css_px(self.spacing)
        run_spacing = css_px(self.run_spacing)
        justify = {
            WrapAlignment.start: "flex-start",
            WrapAlignment.end: "flex-end",
            WrapAlignment.center: "center",
            WrapAlignment.space_between: "space-between",
            WrapAlignment.space_around: "space-around",
            WrapAlignment.space_evenly: "space-evenly",
        }.get(self.alignment, "flex-start")
        align_content = {
            WrapAlignment.start: "flex-start",
            WrapAlignment.end: "flex-end",
            WrapAlignment.center: "center",
            WrapAlignment.space_between: "space-between",
            WrapAlignment.space_around: "space-around",
            WrapAlignment.space_evenly: "space-evenly",
        }.get(self.run_alignment, "flex-start")
        align_items = {
            WrapCrossAlignment.start: "flex-start",
            WrapCrossAlignment.end: "flex-end",
            WrapCrossAlignment.center: "center",
        }.get(self.cross_axis_alignment, "flex-start")
        direction = "row" if self.direction == Axis.horizontal else "column"
        st.markdown(
            f"""
<style>
div.st-key-{wrap_key} {{
  display: flex !important;
  flex-direction: {direction} !important;
  flex-wrap: wrap !important;
  justify-content: {justify} !important;
  align-content: {align_content} !important;
  align-items: {align_items} !important;
  column-gap: {spacing} !important;
  row-gap: {run_spacing} !important;
}}
</style>
""",
            unsafe_allow_html=True,
        )
