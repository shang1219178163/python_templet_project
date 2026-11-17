from enum import Enum, unique

@unique
class WeekdayEnum(Enum):
    """星期枚举"""
    MON = (1, "星期一")
    TUE = (2, "星期二")
    WED = (3, "星期三")
    THU = (4, "星期四")
    FRI = (5, "星期五")
    SAT = (6, "星期六")
    SUN = (7, "星期日")

    def __new__(cls, value: int, desc: str):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        return obj

    # @classmethod
    # def valueOf(cls, value: int):
    #     """根据值获取枚举"""
    #     for member in cls:
    #         if member.value == value:
    #             return member
    #     raise ValueError(f"无效的值: {value}")
