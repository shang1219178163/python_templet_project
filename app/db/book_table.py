"""图书表的 ORM 模型：只负责映射数据库表，不参与接口进出参。"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BookTable(Base):
    __tablename__ = "book"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_books_stock_non_negative"),
        CheckConstraint("stock <= total_num", name="ck_books_stock_le_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(50))
    publisher: Mapped[str] = mapped_column(String(100), default="")
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    total_num: Mapped[int] = mapped_column(default=0)
    stock: Mapped[int] = mapped_column(default=0)
    is_borrow: Mapped[bool] = mapped_column(default=False)
