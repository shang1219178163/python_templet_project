import json
from typing import Any


def _json_default(obj: Any) -> Any:
    """json 序列化兜底：自定义对象转字典，其余转字符串"""
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    if isinstance(obj, (set, tuple)):
        return list(obj)
    return str(obj)


class ReprMixin:
    """打印信息"""

    # def toDict(self) -> dict[str, Any]:
    #     """模型转字典"""
    #     return self.__dict__

    def __repr__(self) -> str:
        t = f"{type(self)}".replace("__main__.", "")
        return f"{t} {hex(id(self))}:{json.dumps(self.__dict__, ensure_ascii=False, default=_json_default)}"
