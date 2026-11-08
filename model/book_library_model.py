import json
from pathlib import Path

from pydantic import BaseModel, Field

from model.book_model import BookModel

# 默认图书数据路径
BOOKS_JSON_PATH = Path(__file__).resolve().parent.parent / "assets" / "json" / "books.json"


class BookLibraryModel(BaseModel):
    """图书馆模型"""

    books: list[BookModel] = Field(default_factory=list)
    """图书馆藏书列表"""

    def borrow_book(self, book: BookModel) -> bool:
        """借书"""
        idx = next((i for i, e in enumerate(self.books) if e.isbn == book.isbn), -1)
        if idx == -1:
            return False
        self.books[idx].is_borrow = True
        return True

    def return_book(self, book: BookModel) -> bool:
        """还书"""
        idx = next((i for i, e in enumerate(self.books) if e.isbn == book.isbn), -1)
        # values = [e for e in self.books if e.isbn == book.isbn]
        if idx == -1:
            return False
        self.books[idx].is_borrow = False
        return True


    def add_book(self, book: BookModel) -> None:
        """添加图书"""
        self.books.append(book)

    def remove_book(self, book: BookModel) -> None:
        """移除图书"""
        self.books.remove(book)

    def find_book_by_isbn(self, isbn: str) -> BookModel | None:
        """根据ISBN查找图书"""
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def load_books(
        self,
        path: str | Path = BOOKS_JSON_PATH,
        count: int | None = None,
    ) -> list[BookModel]:
        """解析图书 JSON，载入藏书并返回图书列表；count 为 None 时载入全部"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if count is not None:
            data = data[: max(count, 0)]
        self.books = [BookModel.from_dict(item) for item in data]
        return self.books
