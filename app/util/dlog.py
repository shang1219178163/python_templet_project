"""DLog 日志打印。格式：[日期时间][日志类型][文件名.函数名 Line:行]: 日志内容

Python 3.13。调用位置用 ``code.co_qualname``（3.11+）和当前帧行号，
跳过本模块内的封装，使 ``DLog.d`` / ``DLog.center`` 都指向外部调用点。
调用位置统一加文件名前缀（如 ``codable.show_validate Line:36``），模块顶层只显示文件名。
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


class DLog:
    """与 Dart ``DLog`` 对齐的分级日志。"""

    enable_log = True
    enable_color = False

    _ansi_reset = "\x1b[0m"
    _ansi_red = "\x1b[31m"
    _ansi_green = "\x1b[32m"
    _ansi_yellow = "\x1b[33m"
    _ansi_blue = "\x1b[34m"

    def __init__(self, *args: object, sep: str = " ", end: str = "\n") -> None:
        """像 ``print`` 一样调用：按 DEBUG 级别输出，附带调用位置。

        ``from app.util.dlog import DLog as print`` 后可直接 ``print(a, b)``。
        """
        text = sep.join(str(arg) for arg in args)
        DLog._print_log("DEBUG", text, DLog._ansi_blue, end=end)

    @staticmethod
    def d(message: object) -> str:
        """打印调试日志。"""
        return DLog._print_log("DEBUG", message, DLog._ansi_blue)

    @staticmethod
    def i(message: object) -> str:
        """打印信息日志。"""
        return DLog._print_log("INFO", message, DLog._ansi_green)

    @staticmethod
    def w(message: object) -> str:
        """打印警告日志。"""
        return DLog._print_log("WARN", message, DLog._ansi_yellow)

    @staticmethod
    def e(message: object) -> str:
        """打印错误日志。"""
        return DLog._print_log("ERROR", message, DLog._ansi_red)

    @staticmethod
    def center(lines: list[str]) -> None:
        """按最长一行居中后逐行以 DEBUG 输出。"""
        if not lines:
            return
        max_length = max(len(text) for text in lines)

        def line(text: str) -> str:
            fill_count = max_length - len(text)
            left = fill_count // 2
            return f"{' ' * left}{text}{' ' * (fill_count - left)}"

        for text in lines:
            DLog.d(line(text))

    @staticmethod
    def _caller_frame():
        here = DLog._print_log.__code__.co_filename
        frame = sys._getframe(1)
        while frame is not None:
            if frame.f_code.co_filename != here:
                return frame
            frame = frame.f_back
        return None

    @staticmethod
    def _caller_info() -> tuple[str, int]:
        frame = DLog._caller_frame()
        if frame is None:
            return "unknown", 0
        return DLog._caller_name(frame), frame.f_lineno

    @staticmethod
    def _caller_name(frame) -> str:
        """返回「文件名.函数名」，模块顶层只返回文件名（含 .py 后缀）"""
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

    @staticmethod
    def _print_log(level: str, message: object, ansi_color: str, end: str = "\n") -> str:
        """输出一条日志，并返回实际打印的字符串。关闭日志或 ``python -O`` 时返回空串。"""
        if not DLog.enable_log or not __debug__:
            return ""

        caller_name, line_number = DLog._caller_info()
        log_message = (
            f"[{datetime.now()} {level} {caller_name} Line:{line_number}]: {message}"
        )
        if DLog.enable_color:
            log_message = f"{ansi_color}{log_message}{DLog._ansi_reset}"
        print(log_message, end=end)
        return log_message
