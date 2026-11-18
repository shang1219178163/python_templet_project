"""泛型与类型参数演示（Python 3.13，PEP 695 语法）。"""

from typing import Any, Self


# 受约束的类型参数：X 只能是 int 或 str（老写法是 TypeVar("X", int, str)）
def echo[X: (int, str)](value: X) -> X:
    return value


class Box[T]:
    """通用包装器：取值、改值、下标、切片。"""

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

    def set(self, value: T) -> None:
        self.value = value

    def __getitem__(self, index: int | slice) -> T | Self:
        """nums[0] 取单个元素；nums[1:3]、nums[1:4:2] 返回新的 Box。

        步长存放在 Python 传入的 slice 对象里，转发给底层序列即可生效。
        前提是 T 本身可下标（list / tuple / str），否则会 TypeError。
        """
        value: Any = self.value
        if isinstance(index, slice):
            return Box(value[index])
        return value[index]

    def __repr__(self) -> str:
        return f"Box({self.value!r})"


def main() -> None:
    box = Box(42)  # Box[int]
    box2 = Box("hello world!")  # Box[str]
    print(box.get(), box2.get(), echo(1), echo("a"))

    nums = Box(list(range(20)))  # Box[list[int]]
    print(nums[0], nums[-1])  # 0 19
    print(nums[::2])  # 偶数
    print(nums[1::2])  # 奇数
    print(nums[::-1][:3])  # 倒序取前三个
    print(box2[1:3])  # Box('el')


if __name__ == "__main__":
    main()
