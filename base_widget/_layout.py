"""布局组件共用的间距换算。"""

from __future__ import annotations

from typing import Literal


def gap_token(spacing: float | str | None) -> Literal["small", "medium", "large"] | None:
    if spacing is None or spacing == 0 or spacing == "none":
        return None
    if spacing in ("small", "medium", "large"):
        return spacing
    try:
        value = float(spacing)
    except (TypeError, ValueError):
        return "small"
    if value <= 8:
        return "small"
    if value <= 16:
        return "medium"
    return "large"


def streamlit_main_align(alignment: str, *, horizontal: bool) -> str:
    if alignment in ("space_between", "space_around", "space_evenly"):
        return "distribute"
    if alignment == "center":
        return "center"
    if alignment == "end":
        return "right" if horizontal else "bottom"
    return "left" if horizontal else "top"


def streamlit_cross_align(alignment: str, *, horizontal: bool) -> str:
    if alignment in ("center", "baseline"):
        return "center"
    if alignment == "end":
        return "bottom" if horizontal else "right"
    return "top" if horizontal else "left"


def css_px(value: float | str) -> str:
    if isinstance(value, str) and not value.replace(".", "", 1).isdigit():
        token = {
            "small": "8px",
            "medium": "16px",
            "large": "24px",
            "none": "0",
        }
        return token.get(value, value)
    return f"{float(value):g}px"
