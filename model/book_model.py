from typing import Any

from pydantic import BaseModel


class BookModel(BaseModel):
    """图书模型"""

    title: str
    """书名"""

    author: str
    """作者"""

    isbn: str
    """ISBN"""

    is_borrow: bool = False
    """是否已借出"""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BookModel":
        """字典解码为模型"""
        return cls.model_validate(data)

    def __str__(self) -> str:
        return f"BookModel(isbn={self.isbn}, title={self.title}, author={self.author}, is_borrow={self.is_borrow})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BookModel):
            return NotImplemented
        return self.isbn == other.isbn

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, BookModel):
            return NotImplemented
        return self.isbn < other.isbn
