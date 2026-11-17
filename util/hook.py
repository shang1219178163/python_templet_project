from datetime import datetime
from functools import wraps
from pathlib import Path
from types import FunctionType
from typing import Any, Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")

# 回调统一签名：位置参数与被装饰函数一致，额外接收 extra，after/on_error 另加 result
HookCallback = Callable[..., None]


def hook(
    before: HookCallback | None = None,
    after: HookCallback | None = None,
    on_error: HookCallback | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    添加面向切面编程（AOP）；参数签名与返回值类型由 ParamSpec / TypeVar 原样保留
    :param before: 函数执行前回调
    :param after: 函数执行后回调（额外收到 result）
    :param on_error: 抛异常时回调；异常由本装饰器继续抛出，回调内自行处理
    :return: 装饰器，被装饰函数的签名和返回类型保持不变
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # __code__ 只存在于普通函数上，Callable 无法保证，故收窄后取
        code = cast(FunctionType, func).__code__
        filename = Path(code.co_filename).stem  # 函数定义所在文件（无扩展名）
        lineno = code.co_firstlineno  # 函数定义所在行号
        func_name = code.co_name  # 函数名
        # //[log] [时间戳 文件名.方法名 Line:行]:
        extra: list[str] = [f"{filename}.{func_name}", f"Line:{lineno}"]

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if before:
                before(*args, extra=extra, **kwargs)
            try:
                result = func(*args, **kwargs)
            except Exception:
                if on_error:
                    on_error(*args, extra=extra, **kwargs)  # 统一签名，异常信息自行闭包获取
                raise
            if after:
                after(*args, extra=extra, result=result, **kwargs)
            return result

        return wrapper

    return decorator


def on_before(*args: Any, extra: list[str], **kwargs: Any) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"[{date_str} before {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]")


def on_after(*args: Any, extra: list[str], result: Any, **kwargs: Any) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"[{date_str} after  {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]: {result}")


# 测试代码
if __name__ == "__main__":

    @hook(before=on_before, after=on_after)
    def add(a: int, b: int) -> int:
        return a + b

    print(add(1, 2))

    # 类型层面 add 仍是 (a: int, b: int) -> int：
    # add("1", 2) 会被类型检查器标红，运行时才抛 TypeError
