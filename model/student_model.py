
from dataclasses import asdict, dataclass
from typing import Any

@dataclass
class StudentModel:

    student_id: str
    """学号"""

    name: str
    """姓名"""

    chinese: int
    """语文"""

    math: int
    """数学"""

    english: int
    """英语"""

    @property
    def total_score(self) -> int:
        """总分"""
        return sum([self.chinese, self.math, self.english])

    @property
    def average_score(self) -> float:
        """平均分"""
        return round(self.total_score / 3, 2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudentModel":
        """字典解码为模型"""
        return cls(
            student_id=data["student_id"],
            name=data["name"],
            chinese=data["chinese"],
            math=data["math"],
            english=data["english"],
        )

    def to_dict(self) -> dict[str, Any]:
        """模型转字典"""
        data = asdict(self)
        return data

    def __str__(self) -> str:
        return f"StudentModel(student_id={self.student_id}, name={self.name}, "

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StudentModel):
            return NotImplemented
        return self.student_id == other.student_id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, StudentModel):
            return NotImplemented
        return self.student_id < other.student_id