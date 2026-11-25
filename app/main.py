"""FastAPI 应用入口：创建应用、注册 lifespan、路由与异常处理。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import book as book_routes
from app.db.init import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表；空库时写入示例图书（学习阶段用，正式项目请改用 Alembic）"""
    init_db()
    yield


app = FastAPI(title="图书信息查询系统", lifespan=lifespan)
app.include_router(book_routes.router)
register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
