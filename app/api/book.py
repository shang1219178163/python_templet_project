import asyncio
from decimal import Decimal
from time import time

import uvicorn
from fastapi import FastAPI

from api.api_response import ApiResponse
from app.model.book import Book

app = FastAPI(title="图书信息查询系统")


@app.get("/", summary="欢迎信息", response_model=ApiResponse)
def read_root() -> ApiResponse:
    """欢迎信息"""
    return ApiResponse(
        code=200,
        message="欢迎使用图书信息查询系统!",
        data=None
    )


@app.get("/books", summary="获取所有图书列表", response_model=ApiResponse[list[Book]])
def get_books() -> ApiResponse[list[Book]]:
    """图书列表"""
    return ApiResponse(
        code=200,
        message="success",
        data=[
            Book(
                title="算法导论",
                author="Thomas H. Cormen",
                isbn="9787111000013",
                price=Decimal("66"),
            ),
            Book(
                title="计算机程序设计艺术",
                author="Donald E. Knuth",
                isbn="9787302000020",
                price=Decimal("77"),
            ),
            Book(
                title="深入理解计算机系统",
                author="Randal E. Bryant",
                isbn="9787040000030",
                price=Decimal("88"),
            ),
        ],
    )


@app.get("/books/count", summary="获取图书总数", response_model=ApiResponse[dict[str, int]])
def book_count() -> ApiResponse[dict[str, int]]:
    """图书总数"""
    return ApiResponse(
        code=200,
        message="欢迎使用图书信息查询系统!",
        data={"total": 20}
    )


@app.get("/slow", summary="异步测试", response_model=ApiResponse[dict[str, int]])
async def asyncTest():
    t1 = time()
    # 耗时请求操作I0操作，await关键字
    # 用了await关键字，就必须在async修饰的函数
    await asyncio.gather(
        mock_async_task(),
        mock_async_task(),
        mock_async_task()
    )
    cost = round(time() - t1, 2)
    print(cost)
    return ApiResponse(
        code=200,
        message="欢迎使用图书信息查询系统!",
        data={"耗时": cost}
    )


async def mock_async_task():
    print('开始查询数据库')
    await asyncio.sleep(3)
    print('完成数据查询')


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
