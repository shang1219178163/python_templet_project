from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from mixins.repr_mixin import ReprMixin


class Book(BaseModel, ReprMixin):
    """图书模型"""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: int = Field(default=0, ge=0, description="图书ID")
    title: str = Field(min_length=1, max_length=100, description="书名")
    author: str = Field(min_length=1, max_length=50, description="作者")
    isbn: str = Field(pattern=r"^\d{13}$", description="ISBN，唯一标识")
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

    @field_serializer("price", when_used="json")
    def _serialize_price(self, price: Decimal) -> str:
        """JSON 中统一按两位小数输出，避免前端再做浮点格式化"""
        return f"{price:.2f}"
