"""数据库模块：连接、会话、ORM 基类、表模型与初始化脚本都放在这里。

SQLite 库文件默认放在项目根目录的 `data/app.db`（与代码包分离），
可用环境变量 `DATABASE_URL` 换成 MySQL / PostgreSQL（见 `app/config.py`）。
"""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# app/db/__init__.py -> app/db -> app -> 项目根目录
DB_DIR = Path(__file__).resolve().parents[2] / "data"
DB_FILE = DB_DIR / "app.db"
if not settings.database_url:
    # 默认 SQLite 模式下确保数据目录存在
    DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = settings.database_url or f"sqlite:///{DB_FILE}"
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    echo=settings.sql_echo,
    # SQLite 默认禁止跨线程复用连接，FastAPI 的同步接口跑在线程池里，需要关掉该检查
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    # MySQL 等长连接可能被服务端断开，取连接前先探活；SQLite 本地文件不需要
    pool_pre_ping=not IS_SQLITE,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 表模型的基类"""


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：每个请求一个会话，请求结束自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
