"""AOP 装饰器：打印函数调用的参数与返回值。"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from types import FunctionType
from typing import cast

# (文件名.函数名, Line:行号)
type HookExtra = tuple[str, str]


def log[**P, R]() -> Callable[[Callable[P, R]], Callable[P, R]]:
    """添加面向切面编程（AOP）。

    参数签名与返回值类型由 PEP 695 的 `**P` / `R` 原样保留。
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
            result = func(*args, **kwargs)
            print(f"[{_now()} {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]: {result}")
            return result

        return wrapper

    return decorator


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


# 测试代码
if __name__ == "__main__":

    @log()
    def add(a: int, b: int) -> int:
        return a + b

    print(add(1, 2))
