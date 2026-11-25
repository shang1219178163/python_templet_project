"""图书接口的进模型与出模型。

- `BookCreate` / `BookUpdate`：进模型，只做格式校验，不对应数据库表。
- `BookOut`：出模型，负责字段裁剪与 JSON 序列化，可直接从 ORM 对象转换。
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

ISBN_PATTERN = r"^\d{13}$"


class BookBase(BaseModel):
    """进模型与出模型的公共字段，只被继承，不直接使用"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100, description="书名")
    author: str = Field(min_length=1, max_length=50, description="作者")
    publisher: str = Field(default="", max_length=100, description="出版社")
    isbn: str = Field(pattern=ISBN_PATTERN, description="ISBN，唯一标识")
    price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="价格(范围 0 ~ 999999.99，精度到分)",
    )
    total_num: int = Field(default=0, ge=0, description="总数")
    stock: int = Field(default=0, ge=0, description="库存数量")
    is_borrow: bool = Field(default=False, description="是否已借出")


class BookCreate(BookBase):
    """进模型：创建图书。没有 id，主键由数据库生成"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class BookUpdate(BaseModel):
    """进模型：局部更新。字段全部可选，配合 exclude_unset 使用"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=100, description="书名")
    author: str | None = Field(default=None, min_length=1, max_length=50, description="作者")
    publisher: str | None = Field(default=None, max_length=100, description="出版社")
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="价格(范围 0 ~ 999999.99，精度到分)",
    )
    total_num: int | None = Field(default=None, ge=0, description="总数")
    stock: int | None = Field(default=None, ge=0, description="库存数量")
    is_borrow: bool | None = Field(default=None, description="是否已借出")


class BookOut(BookBase):
    """出模型：响应。from_attributes 才能从 ORM 对象直接转换"""

    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    id: int = Field(ge=0, description="图书ID")

    @field_serializer("price", when_used="json")
    def _serialize_price(self, price: Decimal) -> str:
        """JSON 中统一按两位小数输出，避免前端再做浮点格式化"""
        return f"{price:.2f}"
