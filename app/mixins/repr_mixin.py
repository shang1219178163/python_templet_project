import json


class ReprMixin:
    """打印信息"""
    
    # def toDict(self) -> dict[str, Any]:
    #     """模型转字典"""
    #     return self.__dict__

    def __repr__(self) -> str:
        return f"{type(self)} {hex(id(self))}:{json.dumps(self.__dict__, ensure_ascii=False)}"
