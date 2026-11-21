from collections.abc import Callable
from enum import Enum
from typing import Any, Self


class BaseEnum(Enum):
    """
    增强枚举基类

    成员定义: `ACTIVE = (code, label[, extra])`
    - code : 状态码，同时作为枚举的 value，支持 `UserStatus(1)` 直接查找
    - label: 状态描述
    - extra: 补充属性，可以是任意数据，也可以是函数
    """

    code: int
    label: str
    extra: Any

    def __new__(cls, code: int, label: str, extra: Any = None) -> Self:
        obj: Any = object.__new__(cls)
        obj._value_ = code
        obj.code = code
        obj.label = label
        obj.extra = extra
        return obj

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        codes = [m.code for m in cls.__members__.values()]  # 含别名，别用 list(cls)
        dup = sorted({c for c in codes if codes.count(c) > 1})
        if dup:
            raise ValueError(f"{cls.__name__} 存在重复 code: {dup}")

    def call_extra(self, *args: Any, **kwargs: Any) -> Any:
        """调用函数型 extra；不是函数时原样返回，调用处无需 getattr / 判空"""
        return self.extra(*args, **kwargs) if callable(self.extra) else self.extra

    @classmethod
    def match_of(cls, cb: Callable[[Self], bool]) -> Self | None:
        return next((e for e in cls if cb(e)), None)

    @classmethod
    def name_of(cls, name: str) -> Self | None:
        return cls.__members__.get(name)

    @classmethod
    def code_of(cls, code: int) -> Self | None:
        try:
            return cls(code)
        except ValueError:
            return None

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        """给前端下拉框用的 (code, label) 列表"""
        return [(m.code, m.label) for m in cls]
