from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.enums.member_level_enum import MemberLevelEnum


class Student(BaseModel):
    """学生模型"""

    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str = Field(min_length=1, description="学号")
    name: str = Field(
        validation_alias=AliasChoices("name", "userName", "user_name"),
        min_length=1,
        description="姓名",
    )
    chinese: int = Field(ge=0, le=100, description="语文")
    math: int = Field(ge=0, le=100, description="数学")
    english: int = Field(ge=0, le=100, description="英语")
    member_level: MemberLevelEnum = Field(default=MemberLevelEnum.NORMAL, description="图书馆会员等级")
    borrowed_books: list[str] = Field(default_factory=list, description="已借图书列表")
    library_password: str = Field(default="", repr=False, description="图书馆密码（不在 repr 中显示）")

    @property
    def total_score(self) -> int:
        """总分"""
        return sum([self.chinese, self.math, self.english])

    @property
    def average_score(self) -> float:
        """平均分"""
        return round(self.total_score / 3, 2)
