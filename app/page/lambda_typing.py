"""lambda 语法本身不支持类型注解，本文件演示 5 种让类型检查器（mypy / pyright / PyCharm）认识 lambda 参数类型的写法。

直接运行本文件即可看到全部运行时结果；参数被推断成什么类型，见每段上方的注释。
"""

import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import cast

# 本文件在 app/page/ 下，导入 app 包需要先把项目根目录加入 sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 1. 赋值时标注 Callable：x 被推断为 int，返回值被检查为 str
to_str_v1: Callable[[int], str] = lambda x: str(x)


# 2. 由函数参数提供上下文：a、b 被推断为 int
def apply(fn: Callable[[int, int], int]) -> int:
    return fn(2, 3)


# 3. 内置高阶函数的上下文：s 被推断为 str
words = ["b", "A", "c"]

# 4. 推断不出来时用 cast 强制标明（只影响静态检查，运行期无动作）
to_str_v2 = cast(Callable[[int], str], lambda x: str(x))


# 5. 用 def 替代 lambda：唯一能真正写注解的形式，可读性也最好
def to_str_v3(x: int) -> str:
    return str(x)


# 附：functools.partial 会保留原函数的注解
def power(base: int, exp: int) -> int:
    return int(base ** exp)  # int ** int 在类型检查器里返回 Any，显式包一层


square = partial(power, exp=2)


def run_demo() -> None:
    print("== 1. Callable 标注后赋值 ==")
    print("to_str_v1(42):", to_str_v1(42))

    print("\n== 2. 函数参数上下文 ==")
    print("apply(lambda a, b: a + b):", apply(lambda a, b: a + b))
    print("apply(lambda a, b: a * b):", apply(lambda a, b: a * b))

    print("\n== 3. 内置高阶函数 ==")
    words.sort(key=lambda s: s.lower())
    print("sort 后:", words)
    print("map 大写:", list(map(lambda s: s.upper(), words)))

    print("\n== 4. cast 强制标注 ==")
    print("to_str_v2(42):", to_str_v2(42))

    print("\n== 5. def 替代 ==")
    print("to_str_v3(42):", to_str_v3(42))
    print("to_str_v3.__annotations__:", to_str_v3.__annotations__)

    print("\n== 附. partial 保留注解 ==")
    print("square(5):", square(5))
    print("power.__annotations__:", power.__annotations__)

    print("\n== 运行时事实 ==")
    print("lambda 的 __annotations__ 永远是空字典:", (lambda x: x).__annotations__)
    print("cast 不写入注解，只给检查器看:", getattr(to_str_v2, "__annotations__", {}))


run_demo()
