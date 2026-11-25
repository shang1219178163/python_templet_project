"""数据库初始化：建表、补列，并在空库时从 JSON 数据源写入示例图书。

数据源：`app/assets/json/books.json`
执行：uv run python -m app.db.init
"""

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.db.book_table import BookTable

BOOKS_JSON = Path(__file__).resolve().parents[1] / "assets" / "json" / "books.json"
PUBLISHER_COLUMN_SQL = "ALTER TABLE books ADD COLUMN publisher VARCHAR(100) NOT NULL DEFAULT ''"


def load_seed_books(path: Path = BOOKS_JSON) -> list[dict]:
    """读取 JSON 数据源，转换为 ORM 写入所需的字典"""
    items = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "title": item["title"],
            "author": item["author"],
            "publisher": item.get("publisher", ""),
            "isbn": item["isbn"],
            "price": Decimal(str(item["price"])),
            "total_num": int(item["total_num"]),
            "stock": int(item["stock"]),
        }
        for item in items
    ]


def init_db() -> None:
    """建表、补列，空库时写入示例数据，可重复执行"""
    Base.metadata.create_all(engine)
    _ensure_schema()
    with SessionLocal() as db:
        _seed(db)


def _ensure_schema(target_engine=engine) -> None:
    """create_all 不会修改已有表，这里给旧库补 publisher 列"""
    if "publisher" in {col["name"] for col in inspect(target_engine).get_columns("books")}:
        return
    try:
        with target_engine.begin() as conn:
            conn.execute(text(PUBLISHER_COLUMN_SQL))
    except SQLAlchemyError:
        # 多 worker 同时启动时，另一个进程可能已经加过列
        if "publisher" not in {col["name"] for col in inspect(target_engine).get_columns("books")}:
            raise


def _seed(db: Session) -> None:
    if db.scalar(select(BookTable.id).limit(1)) is not None:
        return
    db.add_all([BookTable(**book) for book in load_seed_books()])
    try:
        db.commit()
    except IntegrityError:
        # 多 worker 同时播种时，后提交者会撞 ISBN 唯一约束，回滚即可
        db.rollback()


if __name__ == "__main__":
    init_db()
    print(f"数据库与数据表已就绪（种子数据 {len(load_seed_books())} 本）")
