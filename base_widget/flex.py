"""Flutter Flex / Row / Column 的 Streamlit 封装。

子组件沿主轴排列，空间不够时不换行，而是收缩或横向滚动。
"""

from __future__ import annotations

from types import TracebackType
from typing import Literal

import streamlit as st

from base_widget._layout import css_px, gap_token, streamlit_cross_align, streamlit_main_align
from base_widget._style import inject_css
from base_widget.axis import Axis


class MainAxisAlignment:
    start = "start"
    end = "end"
    center = "center"
    space_between = "space_between"
    space_around = "space_around"
    space_evenly = "space_evenly"


class CrossAxisAlignment:
    start = "start"
    end = "end"
    center = "center"
    stretch = "stretch"
    baseline = "baseline"


class MainAxisSize:
    min = "min"
    max = "max"


_JUSTIFY = {
    MainAxisAlignment.start: "flex-start",
    MainAxisAlignment.end: "flex-end",
    MainAxisAlignment.center: "center",
    MainAxisAlignment.space_between: "space-between",
    MainAxisAlignment.space_around: "space-around",
    MainAxisAlignment.space_evenly: "space-evenly",
}

_ALIGN_ITEMS = {
    CrossAxisAlignment.start: "flex-start",
    CrossAxisAlignment.end: "flex-end",
    CrossAxisAlignment.center: "center",
    CrossAxisAlignment.stretch: "stretch",
    CrossAxisAlignment.baseline: "baseline",
}


class Flex:
    """弹性布局，对齐 Flutter ``Flex``。

    用法::

        with Flex(direction=Axis.horizontal, spacing=8):
            st.button("左")
            st.button("右")
    """

    def __init__(
        self,
        *,
        direction: str = Axis.horizontal,
        main_axis_alignment: str = MainAxisAlignment.start,
        cross_axis_alignment: str = CrossAxisAlignment.center,
        main_axis_size: str = MainAxisSize.max,
        spacing: float | str = 0,
        border: bool = False,
        width: int | Literal["stretch", "content"] | None = None,
        height: int | Literal["stretch", "content"] | None = None,
        key: str | None = None,
    ) -> None:
        self.direction = direction
        self.main_axis_alignment = main_axis_alignment
        self.cross_axis_alignment = cross_axis_alignment
        self.main_axis_size = main_axis_size
        self.spacing = spacing
        self.border = border
        self.width = width
        self.height = height
        self.key = key
        self._container = None

    def __enter__(self):
        horizontal = self.direction == Axis.horizontal
        main_align = streamlit_main_align(self.main_axis_alignment, horizontal=horizontal)
        cross_align = streamlit_cross_align(self.cross_axis_alignment, horizontal=horizontal)
        fill = self.main_axis_size == MainAxisSize.max
        width = self.width
        if width is None:
            width = "stretch" if fill or not horizontal else "content"
        height = self.height
        if isinstance(height, int):
            height = "content"
        elif height is None:
            height = "stretch" if fill and not horizontal else "content"
        flex_key = self.key or f"flutter_flex_{id(self)}"
        self._inject_css(flex_key)
        kwargs = {
            "key": flex_key,
            "horizontal": horizontal,
            "gap": gap_token(self.spacing),
            "horizontal_alignment": main_align if horizontal else cross_align,
            "vertical_alignment": cross_align if horizontal else main_align,
            "width": width,
            "height": height,
            "border": self.border,
        }
        if horizontal:
            kwargs["wrap"] = False
        self._container = st.container(**kwargs)
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

    def _inject_css(self, flex_key: str) -> None:
        spacing = css_px(self.spacing)
        justify = _JUSTIFY.get(self.main_axis_alignment, "flex-start")
        align_items = _ALIGN_ITEMS.get(self.cross_axis_alignment, "center")
        direction = "row" if self.direction == Axis.horizontal else "column"
        if isinstance(self.height, int):
            size_rule = (
                f"height: {self.height}px !important; "
                f"min-height: {self.height}px !important; "
                "flex: none !important; "
                "overflow: visible !important;"
            )
        elif self.main_axis_size == MainAxisSize.max:
            size_rule = (
                "width: 100% !important;"
                if self.direction == Axis.horizontal
                else "align-self: stretch !important; min-height: 100% !important;"
            )
        elif self.direction == Axis.horizontal:
            size_rule = (
                "width: fit-content !important; "
                "max-width: 100% !important; "
                "align-self: flex-start !important;"
            )
        else:
            size_rule = "height: fit-content !important;"
        inject_css(
            f"""
div.st-key-{flex_key} {{
  display: flex !important;
  flex-direction: {direction} !important;
  flex-wrap: nowrap !important;
  justify-content: {justify} !important;
  align-items: {align_items} !important;
  gap: {spacing} !important;
  {size_rule}
}}
"""
        )


class Row(Flex):
    """水平弹性布局，对齐 Flutter ``Row``。"""

    def __init__(
        self,
        *,
        main_axis_alignment: str = MainAxisAlignment.start,
        cross_axis_alignment: str = CrossAxisAlignment.center,
        main_axis_size: str = MainAxisSize.max,
        spacing: float | str = 0,
        border: bool = False,
        width: int | Literal["stretch", "content"] | None = None,
        height: int | Literal["stretch", "content"] | None = None,
        key: str | None = None,
    ) -> None:
        super().__init__(
            direction=Axis.horizontal,
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
            main_axis_size=main_axis_size,
            spacing=spacing,
            border=border,
            width=width,
            height=height,
            key=key,
        )


class Column(Flex):
    """垂直弹性布局，对齐 Flutter ``Column``。"""

    def __init__(
        self,
        *,
        main_axis_alignment: str = MainAxisAlignment.start,
        cross_axis_alignment: str = CrossAxisAlignment.center,
        main_axis_size: str = MainAxisSize.max,
        spacing: float | str = 0,
        border: bool = False,
        width: int | Literal["stretch", "content"] | None = None,
        height: int | Literal["stretch", "content"] | None = None,
        key: str | None = None,
    ) -> None:
        super().__init__(
            direction=Axis.vertical,
            main_axis_alignment=main_axis_alignment,
            cross_axis_alignment=cross_axis_alignment,
            main_axis_size=main_axis_size,
            spacing=spacing,
            border=border,
            width=width,
            height=height,
            key=key,
        )
