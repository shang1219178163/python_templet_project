import inspect
from typing import Any, Self, cast, get_args, get_origin, get_type_hints


def _dump(value: Any) -> Any:
    """序列化：模型转字典，list / dict 递归处理"""
    if isinstance(value, SerializableMixin):
        return value.to_dict()
    if isinstance(value, (list, tuple)):
        return [_dump(e) for e in value]
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    return value


def _decode(hint: Any, value: Any) -> Any:
    """反序列化：按类型注解把 dict 还原成模型或模型列表"""
    if get_origin(hint) is list:
        (item_type,) = get_args(hint)
        return [_decode(item_type, e) for e in value]
    if isinstance(hint, type) and issubclass(hint, SerializableMixin) and isinstance(value, dict):
        return hint.from_dict(value)
    return value


class SerializableMixin:
    """模型与字典互转的通用封装

    - to_dict：遍历实例属性，去掉私有字段的名字修饰（_BookNew__stock → stock），嵌套模型与列表递归展开
    - from_dict：按 __init__ 形参过滤构造；类注解声明的非构造字段（如 books）还原后 setattr
    """

    def to_dict(self, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
        """模型转字典，exclude 中的字段不输出"""
        prefix = f"_{type(self).__name__}__"
        return {
            k.removeprefix(prefix): _dump(v) for k, v in vars(self).items() if k.removeprefix(prefix) not in exclude
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """按构造形参过滤后构造实例，注解声明的非构造字段还原后赋值"""
        # 取出 __init__ 的形参名集合，并去掉 self
        params = set(inspect.signature(cls.__init__).parameters) - {"self"}
        # 只保留构造器认识的字段，多余的（如只读的 stock）先丢弃
        kwargs = {k: v for k, v in data.items() if k in params}
        # cls 推断为 type[Self]，PyCharm 会按其自身 __init__ 校验而误报意外实参
        obj = cast(type[Any], cls)(**kwargs)

        # 读取类上声明的类型注解，用于还原非构造字段
        hints = get_type_hints(cls)
        # 再遍历原始数据，处理构造器之外的字段
        for k, v in data.items():
            # 跳过构造参数（已传入）和没有注解的字段（无法判断目标类型）
            if k in params or k not in hints:
                continue
            # 按注解声明的类型还原（如 list[BookNew]）后赋给实例
            setattr(obj, k, _decode(hints[k], v))
        # 返回构造完成的实例
        return obj
