# ORM 进模型 / 出模型最佳实践

> 适用：本项目（Python 3.13 + FastAPI + pydantic 2.x + SQLAlchemy 2.x）。
> 相关文档：[SQLAlchemy创建数据库.md](./SQLAlchemy创建数据库.md)。

## 一、核心结论

**ORM 表模型、进模型、出模型必须拆开，不能让一个 `Book` 同时承担三种职责。**

拆分前常见问题：

- 创建接口允许客户端传 `id`，能绕过数据库自增、覆盖别的记录。
- 更新接口分不清「字段没传」和「字段传了 null」，用 `exclude_none` 又会吞掉主动清空的意图。
- 响应模型和表结构绑死，表里加个内部字段（密码、软删标记）就可能被带出接口。

落地后的分层：

| 层             | 类名         | 位置                   | 职责                 | 禁止                        |
|----------------|--------------|------------------------|----------------------|-----------------------------|
| ORM 表模型     | `BookTable`  | `app/db/book_table.py` | 映射表、承载查询     | 出现在接口参数或返回值里    |
| 进模型（创建） | `BookCreate` | `app/dto/book.py`      | 校验客户端提交       | 出现 `id`                   |
| 进模型（更新） | `BookUpdate` | `app/dto/book.py`      | 局部更新，字段全可选 | 出现不可变字段（如 `isbn`） |
| 出模型（响应） | `BookOut`    | `app/dto/book.py`      | 字段裁剪 + 序列化    | 暴露敏感 / 内部字段         |

一句话原则：

> 进模型只做「格式校验」，出模型只做「字段裁剪 + 序列化」，ORM 只做「表映射」，三者之间在 service 层显式转换。

---

## 二、进模型 / 出模型的写法

```python
# app/dto/book.py
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

ISBN_PATTERN = r"^\d{13}$"


class BookBase(BaseModel):
    """进出模型的公共字段，只被继承，不直接使用"""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100, description="书名")
    author: str = Field(min_length=1, max_length=50, description="作者")
    isbn: str = Field(pattern=ISBN_PATTERN, description="ISBN，唯一标识")
    price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=8, decimal_places=2)
    total_num: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    is_borrow: bool = Field(default=False)


class BookCreate(BookBase):
    """进模型：创建。没有 id，主键由数据库生成"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class BookUpdate(BaseModel):
    """进模型：局部更新。字段全部可选"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=100)
    author: str | None = Field(default=None, min_length=1, max_length=50)
    price: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    total_num: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    is_borrow: bool | None = Field(default=None)


class BookOut(BookBase):
    """出模型：响应。from_attributes 才能从 ORM 对象转换"""
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    id: int = Field(ge=0, description="图书ID")

    @field_serializer("price", when_used="json")
    def _serialize_price(self, price: Decimal) -> str:
        """JSON 中统一按两位小数输出，避免前端再做浮点格式化"""
        return f"{price:.2f}"
```

要点：

- `BookCreate` **没有 `id`**，从类型层面杜绝客户端指定主键。
- `BookUpdate` 全是 `T | None`，配合 `exclude_unset=True`，区分「没传」和「传了 null」。
- `from_attributes=True` **只加在出模型上**；进模型是从字典/JSON 解析，不需要。
- 进模型加 `extra="forbid"`，前端字段拼错会立刻 422，而不是被静默丢弃。
- `str_strip_whitespace` 放基类，进出统一去掉首尾空格。

---

## 三、ORM 表模型：约束下沉到数据库

```python
# app/db/book_table.py
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
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    total_num: Mapped[int] = mapped_column(default=0)
    stock: Mapped[int] = mapped_column(default=0)
    is_borrow: Mapped[bool] = mapped_column(default=False)
```

**校验分三处，不要混：**

| 校验类型           | 放哪               | 例子                   |
|--------------------|--------------------|------------------------|
| 格式 / 类型 / 范围 | 进模型（pydantic） | ISBN 13 位、价格非负   |
| 数据库级不变量     | ORM 约束 + 迁移    | 库存 ≤ 总数、ISBN 唯一 |
| 业务规则 / 跨表    | service 层         | 已借出的书不能删       |

---

## 四、转换只发生在 service 层

服务方法收在 `BookService` 类中，`db` 由构造参数注入，业务方法不再重复接收：

```python
# app/db_service/book_service.py
class BookService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _to_out(row: BookTable) -> BookOut:
        """ORM 对象 -> 出模型"""
        return BookOut.model_validate(row)

    def create_book(self, payload: BookCreate) -> BookOut:
        self._check_stock(payload.total_num, payload.stock)
        row = BookTable(**payload.model_dump())  # 进模型 -> ORM
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise BookConflictError(f"ISBN {payload.isbn} 已存在") from exc
        self.db.refresh(row)  # 拿到自增 id
        return self._to_out(row)  # ORM -> 出模型

    def update_book(self, book_id: int, payload: BookUpdate) -> BookOut:
        row = self.db.get(BookTable, book_id)
        if row is None:
            raise BookNotFoundError(f"图书 {book_id} 不存在")

        changes = payload.model_dump(exclude_unset=True)  # 只取真正提交的字段
        self._check_stock(changes.get("total_num", row.total_num), changes.get("stock", row.stock))
        for key, value in changes.items():
            setattr(row, key, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise BookConflictError("更新后的数据违反数据库约束") from exc
        self.db.refresh(row)
        return self._to_out(row)
```

接口层只碰 DTO，不碰 ORM；业务异常直接往上抛，由全局异常处理器统一包装：

```python
router = APIRouter()


@router.post("/books", response_model=ApiResponse[BookOut], status_code=201)
def create_book(payload: BookCreate, service: BookServiceDep):
    return ApiResponse(code=201, message="created", data=service.create_book(payload))
```

`BookServiceDep` 定义在 `app/api/deps.py`，内部用 `Depends` 把请求级 `Session` 注入 `BookService`，路由无需自己创建实例。

出模型有 `from_attributes=True`，`BookOut.model_validate(orm_row)` 一行完成转换，不需要手写字段搬运。

---

## 五、最容易踩的坑

1. **直接用 ORM 对象当 `response_model`**：懒加载关系会触发 N+1，敏感字段一加进表就可能被带出去。先在 service 转成
   `BookOut` 再返回，契约更清晰，也方便非 HTTP 场景复用。
2. **一个模型同时当进/出模型**：创建能传 `id`、更新分不清「没传」和「传 null」、响应裁不了字段。
3. **更新用 `exclude_none=True`**：会把「主动清空字段」的意图吞掉，一律用 `exclude_unset=True`。
4. **在 ORM 模型上写 pydantic 校验**：ORM 是数据映射，不是校验层。要合一只能用 `SQLModel`，但会把接口契约和表结构焊死，表结构一改接口就变；本项目已有
   pydantic 体系， **不建议引入 SQLModel**。
5. **出模型继承进模型**：`BookOut(BookCreate)` 会把入参校验带进出参；正确方向是共同字段抽 `BookBase`，进出各自继承。

---

## 六、本项目的落地结构

```
app/
  main.py                  # 创建 FastAPI、注册路由、lifespan 与异常处理
  db/                      # 数据库代码（数据文件不放包内）
    __init__.py            # engine / SessionLocal / Base / get_db
    init.py                # 建表 + 从 app/assets/json/book.json 播种
    book_table.py          # ORM：BookTable
  model/
    book.py                # 旧的纯 pydantic 示例（其他演示页仍在使用）
  dto/
    book.py                # BookBase / BookCreate / BookUpdate / BookOut
    pagination.py          # 通用分页结果 Page[T]
  db_service/
    book_service.py        # BookService：业务规则 + ORM <-> DTO 转换
  api/
    deps.py                # 依赖注入：get_book_service / BookServiceDep
    errors.py              # 全局异常处理，统一 ApiResponse
    routes/
      book.py              # APIRouter，只依赖 DTO 与 service
data/
  app.db                   # SQLite 数据文件，与代码包分离
tests/
  test_book_api.py         # 内存 SQLite 的接口测试
```

小项目可以先不加 `repository/`，service 里直接查库即可；查询逻辑变多再拆。

---

## 七、接口一览

| 方法   | 路径           | 进模型       | 出模型           |
|--------|----------------|--------------|------------------|
| GET    | `/books`       | —            | `Page[BookOut]`  |
| GET    | `/books/count` | —            | `dict[str, int]` |
| GET    | `/books/{id}`  | —            | `BookOut`        |
| POST   | `/books`       | `BookCreate` | `BookOut`        |
| PATCH  | `/books/{id}`  | `BookUpdate` | `BookOut`        |
| DELETE | `/books/{id}`  | —            | `None`           |

错误码约定：不存在 `404`、唯一约束冲突 `409`、业务规则不满足 `422`、字段格式错误由 pydantic 自动返回 `422`。
所有成功与失败响应统一为 `ApiResponse`（`code` / `message` / `data`），由 `app/api/errors.py` 注册的全局异常处理器保证。

`GET /books` 的查询参数由 `PageQuery`（`app/dto/pagination.py`）承载，分页结果使用通用 `Page[T]`：

- 游标分页（默认）：不传 `page` 时走游标分页，`?cursor=上一页最后一条id&page_size=20`；
  首次 `cursor` 可以不传或传空（`?cursor=`），返回 `next_cursor` / `has_more`
- 普通分页：显式传 `?page=1&page_size=20`，返回 `total` / `page` / `has_more`
- 模糊搜索：`?keyword=算法`，在书名 / 作者 / ISBN 中匹配
- 排除数据：`?exclude=1,2` 或 `?exclude=1&exclude=2`，结果不包含这些 id
- `page` 与有值的 `cursor` 同时传会抛 `BookRuleError`，由异常处理器转成 422
