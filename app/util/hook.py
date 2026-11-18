"""AOP 装饰器：在函数执行前、执行后、抛异常时插入回调。"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from types import FunctionType
from typing import Any, cast

# 回调统一签名：位置参数与被装饰函数一致，额外接收 extra；after 另加 result
type HookCallback = Callable[..., None]
# (文件名.函数名, Line:行号)，用元组避免被回调意外改写
type HookExtra = tuple[str, str]


def hook[**P, R](
    before: HookCallback | None = None,
    after: HookCallback | None = None,
    on_error: HookCallback | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """添加面向切面编程（AOP）。

    参数签名与返回值类型由 PEP 695 的 `**P` / `R` 原样保留。
    :param before: 函数执行前回调
    :param after: 函数执行后回调（额外收到 result）
    :param on_error: 抛异常时回调；异常由本装饰器继续抛出，回调内自行处理
    :return: 装饰器，被装饰函数的签名和返回类型保持不变
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # __code__ 只存在于普通函数上，Callable 无法保证，故收窄后取
        code = cast(FunctionType, func).__code__
        extra: HookExtra = (
            f"{Path(code.co_filename).stem}.{code.co_name}",
            f"Line:{code.co_firstlineno}",
        )

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if before is not None:
                before(*args, extra=extra, **kwargs)
            try:
                result = func(*args, **kwargs)
            except Exception:
                if on_error is not None:
                    on_error(*args, extra=extra, **kwargs)  # 统一签名，异常信息自行闭包获取
                raise
            if after is not None:
                after(*args, extra=extra, result=result, **kwargs)
            return result

        return wrapper

    return decorator


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def on_before(*args: Any, extra: HookExtra, **kwargs: Any) -> None:
    print(f"[{_now()} before {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]")


def on_after(*args: Any, extra: HookExtra, result: Any, **kwargs: Any) -> None:
    print(f"[{_now()} after  {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]: {result}")


# 测试代码
if __name__ == "__main__":

    @hook(before=on_before, after=on_after)
    def add(a: int, b: int) -> int:
        return a + b

    print(add(1, 2))

    # 类型层面 add 仍是 (a: int, b: int) -> int：
    # add("1", 2) 会被类型检查器标红，运行时才抛 TypeError
