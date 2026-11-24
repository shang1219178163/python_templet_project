"""模型与字典互转的通用封装(仅标准库)"""

import inspect
import types
from typing import Any, Self, Union, cast, get_args, get_origin, get_type_hints


def _dump(value: Any) -> Any:
    """序列化:模型转字典,容器递归展开"""
    if isinstance(value, SerializableMixin):
        return value.to_dict()
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_dump(e) for e in value]
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    return value


def _decode(hint: Any, value: Any) -> Any:
    """按注解还原:Optional、list / dict / tuple、嵌套模型"""
    if value is None:
        return None

    origin = get_origin(hint)

    # Optional[X] / X | None:取第一个非 None 的分支
    if origin is Union or origin is types.UnionType:
        branches = [a for a in get_args(hint) if a is not type(None)]
        return _decode(branches[0], value) if branches else value

    if origin is list:
        (item,) = get_args(hint)
        return [_decode(item, e) for e in value]
    if origin is dict:
        item_type = get_args(hint)[1]  # JSON 键只能是字符串,只还原值
        return {k: _decode(item_type, v) for k, v in value.items()}
    if origin is tuple:
        args = get_args(hint)
        if args and args[-1] is Ellipsis:
            return tuple(_decode(args[0], e) for e in value)
        return tuple(_decode(h, e) for h, e in zip(args, value))

    if isinstance(hint, type) and issubclass(hint, SerializableMixin) and isinstance(value, dict):
        return hint.from_dict(value)
    return value


class SerializableMixin:
    """模型与字典互转的通用封装

    - to_dict:遍历实例字段,私有字段去掉名字修饰(_BookNew__stock → stock)
    - from_dict:按 __init__ 形参构造;其余字段按类注解或私有属性还原
    """

    def to_dict(self, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
        """模型转字典,exclude 中的字段不输出"""
        prefix = f"_{type(self).__name__}__"
        return {
            k.removeprefix(prefix): _dump(v) for k, v in vars(self).items() if k.removeprefix(prefix) not in exclude
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], strict: bool = False) -> Self:
        """按构造形参过滤后构造实例,其余字段按注解或私有属性还原"""
        # 取出 __init__ 的形参名集合,并去掉 self
        params = set(inspect.signature(cls.__init__).parameters) - {"self"}
        # 只把构造器认识的字段传进去,其余字段构造后再回填
        obj = cast(type[Any], cls)(**{k: v for k, v in data.items() if k in params})

        hints = get_type_hints(cls)
        unknown: list[str] = []
        for k, v in data.items():
            if k in params:
                continue
            # 私有字段/只读属性:写回名字修饰后的底层属性
            attr = f"_{cls.__name__}__{k}"
            if hasattr(obj, attr):
                setattr(obj, attr, _decode(hints.get(k, Any), v))
            elif k in hints and not isinstance(getattr(cls, k, None), property):
                setattr(obj, k, _decode(hints[k], v))
            else:
                unknown.append(k)

        if strict and unknown:
            raise ValueError(f"{cls.__name__} 无法还原的字段: {unknown}")
        return obj
