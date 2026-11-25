# 在项目中创建数据库（SQLite + SQLAlchemy）

> 适用：本项目（Python 3.13 + FastAPI + pydantic）。`/books` 已接入 SQLite，应用入口为 `app/main.py`，路由在 `app/api/routes/book.py`。
> 目标：从零建库、建表，并让接口真正读写数据库。

“创建数据库”在项目里通常包含两件事：

1. **建库**：SQLite 就是生成一个 `.db` 文件；MySQL/PostgreSQL 是在服务端 `CREATE DATABASE`。
2. **建表**：用 ORM 模型定义表结构，再执行 `create_all()` 或迁移脚本生成。

本项目是本地模板/学习项目，推荐 **SQLite + SQLAlchemy 2.0**：零部署、库就是一个文件，PyCharm 可直接连接查看。

---

## 一、安装依赖

```bash
uv add sqlalchemy
```

SQLite 驱动 Python 内置，无需额外安装。

如果想沿用 pydantic 风格，也可以改用 `uv add sqlmodel`（它内含 SQLAlchemy，写法是 pydantic + ORM 合一）。

---

## 二、建库：新建 `app/db/__init__.py`

```python
# app/db/__init__.py
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "app.db"
engine = create_engine(
    f"sqlite:///{DB_FILE}",
    echo=True,  # 想看 SQL 就打开，生产关掉
    connect_args={"check_same_thread": False},  # FastAPI 多线程需要
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有表模型的基类"""


def get_db():
    """FastAPI 依赖：每个请求一个会话，用完自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

这一步还没有真正生成数据库文件——SQLite 是“第一次建表/写入时才创建文件”。

---

## 三、建表：定义 ORM 模型

现有的 `app/model/book.py` 是 **pydantic 校验模型**，建议另建**表模型**，两者职责分开：

- pydantic 模型：接口入参/出参校验、序列化。
- ORM 模型：映射数据库表、承载查询。

```python
# app/db/book_table.py
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BookTable(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(50))
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    total_num: Mapped[int] = mapped_column(default=0)
    stock: Mapped[int] = mapped_column(default=0)
    is_borrow: Mapped[bool] = mapped_column(default=False)
```

---

## 四、生成库文件与数据表

两种时机选一种。

### 方式 1：单独初始化脚本（推荐，可控）

```python
# app/db/init.py
from app.db import Base, engine
import app.db.book_table  # noqa: F401  必须导入，表才会注册到 Base

Base.metadata.create_all(engine)
print("数据库与数据表已就绪")
```

```bash
uv run python -m app.db.init
```

执行后 `data/app.db` 会出现，里面就有 `books` 表。

### 方式 2：FastAPI 启动时自动建表

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
import app.db.book_table  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="图书信息查询系统", lifespan=lifespan)
```

适合学习阶段；正式项目改表结构请用 Alembic 迁移，避免丢数据。

---

## 五、在 FastAPI 接口中使用

```python
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.api_response import ApiResponse
from app.db import get_db
from app.model.book import Book
from app.db.book_table import BookTable


@app.get("/books/db", summary="从数据库获取图书", response_model=ApiResponse[list[Book]])
def list_books(db: Session = Depends(get_db)) -> ApiResponse[list[Book]]:
    rows = db.scalars(select(BookTable)).all()
    return ApiResponse(
        code=200,
        message="success",
        data=[Book.model_validate(row, from_attributes=True) for row in rows],
    )
```

注意：pydantic 的 `Book` 要加 `from_attributes=True`，才能直接从 ORM 对象转换：

```python
model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)
```

---

## 六、查看和管理数据

- **PyCharm 图形化**：右侧 `Database` 面板 → `+` → `Data Source` → `SQLite` → File 选择 `.../python_templet_project/data/app.db` → Test Connection → OK。之后可双击表看数据、写 SQL。
- **命令行**：`sqlite3 data/app.db`，然后 `.tables`、`select * from books;`。

---

## 七、如果要用 MySQL / PostgreSQL

1. 本机或 Docker 起服务，先在服务端建库（MySQL 建议 utf8mb4）：
   `CREATE DATABASE bookdb DEFAULT CHARSET utf8mb4;`（PyCharm Database 控制台或命令行）。
2. 安装驱动。MySQL 的 `pymysql` 已在项目依赖中；PostgreSQL 需另装：

   ```bash
   uv add pymysql                      # MySQL（本项目已包含）
   uv add "psycopg[binary]"            # PostgreSQL
   ```

3. 在 `.env` 或环境变量里配置连接串，而不是改代码：

   ```dotenv
   # MySQL
   DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/bookdb?charset=utf8mb4

   # PostgreSQL
   DATABASE_URL=postgresql+psycopg://user:pass@127.0.0.1:5432/bookdb
   ```

4. 表仍由 `Base.metadata.create_all()` 或 Alembic 生成；重启服务时 `app/db/__init__.py` 会按 `DATABASE_URL` 自动选择方言。
5. 非 SQLite 连接已启用 `pool_pre_ping`，取连接前先探活，避免 MySQL 长连接被服务端断开后报错。

更完整的切换步骤与兼容性说明见 [SQLite与MySQL切换.md](./SQLite与MySQL切换.md)。

---

## 小结

| 步骤 | 做什么 | 产出 |
|---|---|---|
| 1 | `uv add sqlalchemy` | 依赖 |
| 2 | `app/db/__init__.py`：engine / session / Base | 连接与基类 |
| 3 | `app/db/book_table.py`：ORM 模型 | 表定义 |
| 4 | `uv run python -m app.db.init` | `data/app.db` + `books` 表 |
| 5 | 接口里 `Depends(get_db)` | 真正读写数据库 |

后续可选：接入 Alembic 管理表结构变更；把数据访问收进 `app/repository/` 层，接口只依赖仓储接口。
