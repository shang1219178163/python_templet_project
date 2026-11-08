from typing import Any

from pydantic import BaseModel, Field, AliasChoices

from enums.member_level_enum import MemberLevelEnum


class StudentModel(BaseModel):
    """学生模型"""

    student_id: str
    """学号"""

    name: str = Field(
        validation_alias=AliasChoices("name", "userName", "user_name")
    )
    """姓名"""

    chinese: int
    """语文"""

    math: int
    """数学"""

    english: int
    """英语"""

    member_level: MemberLevelEnum = MemberLevelEnum.NORMAL
    """图书馆会员等级"""

    borrowed_books: list[str] = Field(default_factory=list)
    """已借图书列表"""

    library_password: str = Field(default="", repr=False)
    """图书馆密码（不在 repr 中显示）"""

    @property
    def total_score(self) -> int:
        """总分"""
        return sum([self.chinese, self.math, self.english])

    @property
    def average_score(self) -> float:
        """平均分"""
        return round(self.total_score / 3, 2)

    def to_dict(self) -> dict[str, Any]:
        """模型转字典，枚举转为原始值"""
        return self.model_dump(mode="json")

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
