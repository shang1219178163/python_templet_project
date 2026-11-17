import sys
from pathlib import Path
from typing import Any

# 本文件在 lib/page/ 下，往上三级才是项目根目录
project_root = Path(__file__).resolve().parents[2]
project_root_path = str(project_root)
if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

from lib.enums.weekday_enum import WeekdayEnum
from lib.util.dlog import DLog


class CodableModel:
    """可编码模型基类：模型与字典互转"""

    def to_dict(self) -> dict[str, Any]:
        """模型转字典，忽略私有属性"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith("_")
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """字典转模型，只保留构造函数支持的字段"""
        import inspect
        params = inspect.signature(cls.__init__).parameters
        valid_params = [
            name for name in params
            if name != "self" and name not in ("args", "kwargs")
        ]
        filtered_data = {k: v for k, v in data.items() if k in valid_params}
        return cls(**filtered_data)


class Student(CodableModel):
    """学生模型"""

    def __init__(
        self,
        name: str | None = None,
        age: int | None = None,
        avatar: str | None = None,
        weekday: WeekdayEnum | None = None,
    ):
        self.name = name
        self.age = age
        self.avatar = avatar
        self.weekday = weekday

    def __repr__(self):
        weekday_name = self.weekday.name if self.weekday else None
        return f"Student(name={self.name}, age={self.age}, weekday={weekday_name})"


def encode_student(student: Student) -> dict:
    """模型转字典，枚举写成原始值"""
    data = student.to_dict()
    if student.weekday is not None:
        data["weekday"] = student.weekday.value
    return data


def decode_student(data: dict) -> Student:
    """字典转模型，并把星期值还原成枚举"""
    student = Student.from_dict(data)
    weekday = data.get("weekday")
    if weekday is not None:
        student.weekday = WeekdayEnum.valueOf(weekday)
    return student


student = Student(name="张三", age=20, avatar="avatar.jpg", weekday=WeekdayEnum.MON)
encoded = encode_student(student)
decoded = decode_student(encoded)

DLog.d(f"模型: {student}")
DLog.d(f"编码: {encoded}")
DLog.d(f"解码: {decoded}")
if decoded.weekday:
    DLog.d(f"星期: {decoded.weekday.desc}")
