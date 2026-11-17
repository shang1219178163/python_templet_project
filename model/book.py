from typing import Any

from pydantic import BaseModel


class Book(BaseModel):
    """图书模型"""

    id: int = 0
    """图书ID"""

    title: str
    """书名"""

    author: str
    """作者"""

    isbn: str
    """ISBN，唯一标识"""

    price: float = 0.0
    """价格"""

    stock: int = 0
    """库存数量"""

    is_borrow: bool = False
    """是否已借出"""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Book":
        """字典解码为模型"""
        return cls.model_validate(data)

    def __str__(self) -> str:
        return (
            f"Book(isbn={self.isbn}, title={self.title}, author={self.author}, "
            f"price={self.price}, stock={self.stock}, is_borrow={self.is_borrow})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.isbn == other.isbn

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.isbn < other.isbn
