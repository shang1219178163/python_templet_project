"""图书接口路由：只负责解析请求、调用 db_service、返回 DTO。

错误统一由 `app/api/errors.py` 处理，这里不写 try/except。
"""

import asyncio
from time import time

from fastapi import APIRouter

from app.api.api_response import ApiResponse
from app.api.deps import BookServiceDep, PageQueryDep
from app.dto.book import BookCreate, BookOut, BookUpdate
from app.dto.pagination import Page

router = APIRouter()


@router.get("/", summary="欢迎信息", response_model=ApiResponse)
def read_root() -> ApiResponse:
    """欢迎信息"""
    return ApiResponse(
        code=200,
        message="欢迎使用图书信息查询系统!",
        data=None
    )


@router.get(
    "/books",
    summary="获取图书列表（普通分页 / 游标分页）",
    response_model=ApiResponse[Page[BookOut]],
)
def get_books(service: BookServiceDep, query: PageQueryDep) -> ApiResponse[Page[BookOut]]:
    """支持 page/cursor 分页、keyword 模糊搜索、exclude 排除指定 id"""
    data = service.list_books(
        page=query.page,
        cursor=query.cursor,
        page_size=query.page_size,
        keyword=query.keyword,
        exclude=query.exclude,
    )
    return ApiResponse(code=200, message="success", data=data)


@router.get("/books/count", summary="获取图书总数", response_model=ApiResponse[dict[str, int]])
def book_count(service: BookServiceDep) -> ApiResponse[dict[str, int]]:
    """图书总数"""
    return ApiResponse(code=200, message="success", data={"total": service.count_books()})


@router.get("/books/{book_id}", summary="按 ID 获取图书", response_model=ApiResponse[BookOut])
def get_book(book_id: int, service: BookServiceDep) -> ApiResponse[BookOut]:
    """单本图书详情"""
    return ApiResponse(code=200, message="success", data=service.get_book(book_id))


@router.post("/books", summary="新增图书", response_model=ApiResponse[BookOut], status_code=201)
def create_book(payload: BookCreate, service: BookServiceDep) -> ApiResponse[BookOut]:
    """新增图书：请求体是进模型 BookCreate，不接受 id"""
    return ApiResponse(code=201, message="created", data=service.create_book(payload))


@router.patch("/books/{book_id}", summary="局部更新图书", response_model=ApiResponse[BookOut])
def update_book(
    book_id: int,
    payload: BookUpdate,
    service: BookServiceDep,
) -> ApiResponse[BookOut]:
    """局部更新：只修改请求体里出现的字段"""
    return ApiResponse(code=200, message="success", data=service.update_book(book_id, payload))


@router.delete("/books/{book_id}", summary="删除图书", response_model=ApiResponse[None])
def delete_book(book_id: int, service: BookServiceDep) -> ApiResponse[None]:
    """删除图书"""
    service.delete_book(book_id)
    return ApiResponse(code=200, message="deleted", data=None)


@router.get("/slow", summary="异步测试", response_model=ApiResponse[dict[str, float | int]])
async def async_test() -> ApiResponse[dict[str, float | int]]:
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
