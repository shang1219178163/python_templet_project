"""通用分页模型：列表查询参数（PageQuery）与分页结果（Page）分开。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageQuery(BaseModel):
    """列表查询参数：分页 + 模糊搜索 + 排除 id。

    - `keyword`：在书名 / 作者 / ISBN 中做模糊匹配
    - `exclude`：要排除的 id 列表，支持重复参数或逗号分隔
    - 不传 `page` 时走游标分页；`cursor` 首次传空或不传都可以
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    page: int | None = Field(default=None, ge=1, description="页码（普通分页）；不传则走游标分页")
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="每页条数")
    cursor: int | None = Field(default=None, ge=0, description="游标：上一页最后一条 id；首次传空或不传")
    keyword: str | None = Field(
        default=None,
        max_length=100,
        description="模糊搜索：书名 / 作者 / ISBN",
    )
    exclude: list[str] = Field(
        default_factory=list,
        description="要排除的图书 id，可重复传或逗号分隔",
    )

    @field_validator("cursor", mode="before")
    @classmethod
    def _empty_cursor_to_none(cls, value: object) -> object:
        """`?cursor=` 与不传等价，都从游标首页开始"""
        return None if isinstance(value, str) and not value.strip() else value


class Page[T](BaseModel):
    """分页结果。

    - 普通分页：返回 `total` / `page` / `has_more`
    - 游标分页：返回 `next_cursor` / `has_more`
    """

    items: list[T] = Field(description="当前页数据")
    page: int | None = Field(default=None, ge=1, description="当前页码，仅普通分页返回")
    page_size: int = Field(ge=1, description="每页条数")
    total: int | None = Field(default=None, ge=0, description="总条数，仅普通分页返回")
    next_cursor: int | None = Field(default=None, description="下一页游标，仅游标分页返回")
    has_more: bool = Field(description="是否还有下一页")
