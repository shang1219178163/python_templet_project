"""统一异常响应：成功和失败都返回 ApiResponse 结构。

注册方式见 `register_exception_handlers`，由 `app/main.py` 调用。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.api_response import ApiResponse
from app.db_service import book_service

logger = logging.getLogger(__name__)


def _json_response(status_code: int, message: str, data: Any = None) -> JSONResponse:
    payload = ApiResponse(code=status_code, message=message, data=data)
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        return _json_response(exc.status_code, detail)
    return _json_response(exc.status_code, "请求失败", detail)


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _json_response(422, "请求参数校验失败", jsonable_encoder(exc.errors()))


async def _book_not_found_handler(request: Request, exc: book_service.BookNotFoundError) -> JSONResponse:
    return _json_response(404, str(exc))


async def _book_conflict_handler(request: Request, exc: book_service.BookConflictError) -> JSONResponse:
    return _json_response(409, str(exc))


async def _book_rule_handler(request: Request, exc: book_service.BookRuleError) -> JSONResponse:
    return _json_response(422, str(exc))


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return _json_response(500, "服务器内部错误")


def register_exception_handlers(app: FastAPI) -> None:
    """把所有错误都包装成 ApiResponse，前端只需处理一种响应结构"""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(book_service.BookNotFoundError, _book_not_found_handler)
    app.add_exception_handler(book_service.BookConflictError, _book_conflict_handler)
    app.add_exception_handler(book_service.BookRuleError, _book_rule_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
