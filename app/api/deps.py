"""FastAPI 依赖：集中定义可注入对象，路由通过类型别名使用。"""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db_service.book_service import BookService
from app.dto.pagination import PageQuery


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    """每个请求一个 BookService，复用请求级会话"""
    return BookService(db)


BookServiceDep = Annotated[BookService, Depends(get_book_service)]
PageQueryDep = Annotated[PageQuery, Query()]
