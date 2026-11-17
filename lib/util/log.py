from datetime import datetime
from functools import wraps
from pathlib import Path
from types import FunctionType
from typing import Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")

# 回调统一签名：位置参数与被装饰函数一致，额外接收 extra，after/on_error 另加 result
HookCallback = Callable[..., None]


def log() -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    添加面向切面编程（AOP）；参数签名与返回值类型由 ParamSpec / TypeVar 原样保留
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
            result = func(*args, **kwargs)

            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            print(f"[{date_str} {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]: {result}")
            return result

        return wrapper

    return decorator


# 测试代码
if __name__ == "__main__":
    @log()
    def add(a: int, b: int) -> int:
        return a + b


    print(add(1, 2))

    # 类型层面 add 仍是 (a: int, b: int) -> int：
    # add("1", 2) 会被类型检查器标红，运行时才抛 TypeError
