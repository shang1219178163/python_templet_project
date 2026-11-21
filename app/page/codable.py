"""Pydantic V2 四个方法与 `Book` 模型的 JSON 转换演示。

对应文档《Pydantic V2 的 `model_validate` / `model_dump` 命名》里的矩阵：

|              | 从 Python 对象     | 从 JSON 字符串        |
| ------------ | ------------------ | --------------------- |
| 入口（验证） | `model_validate`     | `model_validate_json` |
| 出口（序列化）| `model_dump`        | `model_dump_json`     |

`model_` 前缀是防字段冲突的命名空间，`_json` 后缀区分「JSON 字符串」与「Python 对象」。
"""

import json

from pydantic import ValidationError

from app.model.book import Book
from app.util.dlog import DLog

# 模拟外部输入：price 给字符串，id 故意给 "1"，交给 Pydantic 做验证与类型转换
RAW_DICT = {
    "id": "1",
    "title": "算法导论",
    "author": "Thomas H. Cormen",
    "isbn": "9787111000013",
    "price": "66.60",
    "stock": 5,
}

RAW_JSON = json.dumps(RAW_DICT, ensure_ascii=False)


def show_validate() -> None:
    """入口一：外部 Python 对象 -> 模型，顺带完成类型转换"""
    book = Book.model_validate(RAW_DICT)
    DLog("model_validate ->", book)
    DLog("id 由 '1' 转成 int :", repr(book.id))
    DLog("price 由 str 转 Decimal:", repr(book.price))


def show_validate_json() -> None:
    """入口二：外部 JSON 字符串 -> 模型"""
    book = Book.model_validate_json(RAW_JSON)
    DLog("model_validate_json ->", book.title, "/", book.price)


def show_dump() -> None:
    """出口一：模型 -> Python 数据结构，price 保持 Decimal"""
    data = Book.model_validate(RAW_DICT).model_dump()
    DLog("model_dump ->", data)
    DLog("price 的类型:", type(data["price"]).__name__)


def show_dump_json() -> None:
    """出口二：模型 -> JSON 字符串，price 经 field_serializer 输出两位小数"""
    text = Book.model_validate(RAW_DICT).model_dump_json(indent=2)
    DLog("model_dump_json ->\n" + text)


def show_roundtrip() -> None:
    """往返：模型 -> JSON 字符串 -> 模型，数据不丢"""
    book = Book.model_validate(RAW_DICT)
    restored = Book.model_validate_json(book.model_dump_json())
    DLog("往返后与原模型相等 :", restored == book)


def show_dump_options() -> None:
    """model_dump 的常用参数：排除字段、只保留部分字段"""
    book = Book.model_validate(RAW_DICT)
    DLog("exclude={'stock'} ->", book.model_dump(exclude={"stock"}))
    DLog("include={'title'} ->", book.model_dump(include={"title", "isbn"}))


def show_reject() -> None:
    """非法输入在入口就被拦下，不会流进业务代码"""
    try:
        Book.model_validate(RAW_DICT | {"price": "abc"})
    except ValidationError as e:
        err = e.errors()[0]
        DLog.e(f"非法 price 被拒绝: {err['type']} @ {err['loc']}")
    try:
        Book.model_validate(RAW_DICT | {"isbn": "123"})
    except ValidationError as e:
        err = e.errors()[0]
        DLog.e(f"非法 isbn 被拒绝: {err['type']} @ {err['loc']}")


def run() -> None:
    DLog("开始演示 Book 模型的 JSON 转换")
    show_validate()
    show_validate_json()
    show_dump()
    show_dump_json()
    show_roundtrip()
    show_dump_options()
    show_reject()


run()
