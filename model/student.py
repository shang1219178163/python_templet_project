#!/usr/bin/env python3
"""Student model with dict conversion"""

from typing import Dict, Any, Optional
from enum import Enum, unique

class CodableModel:
    """可编码模型基类"""
    
    def to_dict(self) -> Dict[str, Any]:
        """模型转字典"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """字典转模型"""
        import inspect
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.keys())
        valid_params = [p for p in params if p != 'self' and p not in ('args', 'kwargs')]
        
        filtered_data = {k: v for k, v in data.items() if k in valid_params}
        return cls(**filtered_data)


@unique
class Weekday(Enum):
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
    
    @classmethod
    def from_value(cls, value: int):
        """根据值获取枚举"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"无效的值: {value}")


class Student(CodableModel):
    """学生模型"""
    
    def __init__(self, name: str = None, age: int = None, 
        avatar: str = None, weekday: Weekday = None):
        self.name = name
        self.age = age
        self.avatar = avatar
        self.weekday = weekday
    
    def __repr__(self):
        weekday_name = self.weekday.name if self.weekday else None
        return f"Student(name={self.name}, age={self.age}, weekday={weekday_name})"


# 测试代码
if __name__ == '__main__':
    # 创建学生实例
    student = Student(name="张三", age=20, avatar="avatar.jpg", weekday=Weekday.MON)
    
    # 模型转字典
    dict_data = student.to_dict()
    print("模型转字典:", dict_data)
    
    # 处理枚举值
    if student.weekday:
        dict_data['weekday'] = student.weekday.value
    
    # 字典转模型
    new_student = Student.from_dict(dict_data)
    if 'weekday' in dict_data:
        new_student.weekday = Weekday.from_value(dict_data['weekday'])
    
    print("字典转模型:", new_student)
    print(f"姓名: {new_student.name}, 年龄: {new_student.age}")
    if new_student.weekday:
        print(f"星期: {new_student.weekday.desc}")
