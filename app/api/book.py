from fastapi import FastAPI

from app.model.book import Book

app = FastAPI(title="图书信息查询系统")


@app.get("/", summary="欢迎信息")
def read_root() -> dict[str, str]:
    """欢迎信息"""
    return {"message": "欢迎使用图书信息查询系统!"}


@app.get("/books", summary="获取所有图书列表")
def get_books() -> list[Book]:
    """图书列表"""
    return [
        Book(
            title="算法导论",
            author="Thomas H. Cormen",
            isbn="9787111000013",
            price=66,
        ),
        Book(
            title="计算机程序设计艺术",
            author="Donald E. Knuth",
            isbn="9787302000020",
            price=77,
        ),
        Book(
            title="深入理解计算机系统",
            author="Randal E. Bryant",
            isbn="9787040000030",
            price=88,
        ),
    ]


@app.get("/books/count", summary="获取图书总数")
def book_count() -> dict[str, int]:
    """图书总数"""
    return {"total": 20}
