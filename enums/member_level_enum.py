from enum import Enum, unique


@unique
class MemberLevelEnum(Enum):
    """图书馆会员等级"""
    NORMAL = ("normal", "普通", 0)
    VIP = ("vip", "VIP", 1)

    def __new__(cls, value: str, desc: str, level: int):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        obj.level = level
        return obj

    @classmethod
    def valueOf(cls, value: str):
        """根据值获取枚举"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"无效的值: {value}")
