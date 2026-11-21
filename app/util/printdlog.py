"""printdlog 日志打印。格式：[日期时间 文件名.函数名 Line:行]: 日志内容

像 ``print`` 一样调用；用 ``sys._getframe`` 找到外部调用帧，
跳过本模块内的封装，使调用位置指向真正的调用处。模块顶层只显示文件名。
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import FrameType

enable_log = True
enable_color = False

_ansi_reset = "\x1b[0m"
_ansi_blue = "\x1b[34m"


def printdlog(*args: object, sep: str = " ", end: str = "\n") -> str:
    """像 ``print`` 一样输出，附带调用位置。关闭日志或 ``python -O`` 时返回空串。"""
    if not enable_log or not __debug__:
        return ""

    text = sep.join(str(arg) for arg in args)
    caller_name, line_number = _caller_info()
    message = f"[{datetime.now()} {caller_name} Line:{line_number}]: {text}"
    if enable_color:
        message = f"{_ansi_blue}{message}{_ansi_reset}"
    print(message, end=end)
    return message


def _caller_frame() -> FrameType | None:
    here = printdlog.__code__.co_filename
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_filename != here:
            return frame
        frame = frame.f_back
    return None


def _caller_info() -> tuple[str, int]:
    frame = _caller_frame()
    if frame is None:
        return "unknown", 0
    return _caller_name(frame), frame.f_lineno


def _caller_name(frame: FrameType) -> str:
    """返回「文件名.函数名」，模块顶层只返回文件名（含 .py 后缀）。"""
    filename = Path(frame.f_code.co_filename)
    stem = filename.stem
    qualname = frame.f_code.co_qualname
    if qualname == "<module>":
        return filename.name

    if ".<locals>." in qualname:
        owner, _, function_name = qualname.rpartition(".<locals>.")
        owner_name = owner.split(".")[0]
        if owner_name and owner_name != "<module>":
            return f"{stem}.{owner_name}.{function_name}"
        return f"{stem}.{function_name or 'unknown'}"

    parts = qualname.split(".")
    if len(parts) >= 2:
        return f"{stem}.{parts[-2]}.{parts[-1]}"
    if parts and parts[0]:
        return f"{stem}.{parts[0]}"
    return f"{stem}.unknown"
