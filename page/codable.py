import sys
from pathlib import Path

# 本文件在 page/ 下，上一级才是项目根目录
project_root = Path(__file__).resolve().parent.parent
project_root_path = str(project_root)
if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

from model.student import Student, Weekday
from util.dlog import DLog


def encode_student(student: Student) -> dict:
    """模型转字典，枚举写成原始值。"""
    data = student.to_dict()
    if student.weekday is not None:
        data["weekday"] = student.weekday.value
    return data


def decode_student(data: dict) -> Student:
    """字典转模型，并把星期值还原成枚举。"""
    student = Student.from_dict(data)
    weekday = data.get("weekday")
    if weekday is not None:
        student.weekday = Weekday.from_value(weekday)
    return student


student = Student(name="张三", age=20, avatar="avatar.jpg", weekday=Weekday.MON)
encoded = encode_student(student)
decoded = decode_student(encoded)

DLog.d(f"模型: {student}")
DLog.d(f"编码: {encoded}")
DLog.d(f"解码: {decoded}")
if decoded.weekday:
    DLog.d(f"星期: {decoded.weekday.desc}")
