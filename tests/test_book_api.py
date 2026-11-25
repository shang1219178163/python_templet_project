"""图书接口测试：用内存 SQLite，不读写真实的 data/app.db。

运行方式（项目根目录）：
    python -m unittest tests.test_book_api -v
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.db.book_table import BookTable  # noqa: F401  导入后表才会注册到 Base
from app.db_service import book_service
from app.main import app


class BookApiTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        def override_get_db():
            with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        # 不用 with 包住 TestClient：避免触发 lifespan 去初始化真实的 app.db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _payload(self, **overrides) -> dict:
        data = {
            "title": "算法导论",
            "author": "Thomas H. Cormen",
            "publisher": "机械工业出版社",
            "isbn": "9787111000013",
            "price": "66.00",
            "total_num": 5,
            "stock": 5,
        }
        return {**data, **overrides}

    def _seed(self, count: int) -> list[int]:
        """批量创建图书，返回自增 id 列表"""
        ids = []
        for i in range(count):
            response = self.client.post("/books", json=self._payload(isbn=f"978{i:010d}", title=f"书{i}"))
            self.assertEqual(response.status_code, 201)
            ids.append(response.json()["data"]["id"])
        return ids

    def test_crud(self):
        created = self.client.post("/books", json=self._payload())
        self.assertEqual(created.status_code, 201)
        book = created.json()["data"]
        self.assertGreater(book["id"], 0)
        self.assertEqual(book["price"], "66.00")
        self.assertEqual(book["publisher"], "机械工业出版社")

        listed = self.client.get("/books")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["data"]["items"]), 1)

        count = self.client.get("/books/count")
        self.assertEqual(count.json()["data"]["total"], 1)

        detail = self.client.get(f"/books/{book['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["title"], "算法导论")

        patched = self.client.patch(f"/books/{book['id']}", json={"stock": 3})
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["data"]["stock"], 3)
        self.assertEqual(patched.json()["data"]["total_num"], 5)  # 未提交的字段保持原值

        deleted = self.client.delete(f"/books/{book['id']}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(f"/books/{book['id']}").status_code, 404)

    def test_create_rejects_client_supplied_id(self):
        response = self.client.post("/books", json=self._payload(id=99))
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["code"], 422)
        self.assertIsInstance(body["data"], list)

    def test_duplicate_isbn_returns_409(self):
        self.client.post("/books", json=self._payload())
        response = self.client.post("/books", json=self._payload(title="另一本书"))
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["code"], 409)
        self.assertIn("已存在", body["message"])
        self.assertIsNone(body["data"])

    def test_stock_greater_than_total_returns_422(self):
        response = self.client.post("/books", json=self._payload(total_num=2, stock=3))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], 422)
        self.assertIn("不能大于总数", response.json()["message"])

    def test_invalid_isbn_returns_422(self):
        response = self.client.post("/books", json=self._payload(isbn="123"))
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["code"], 422)
        self.assertEqual(body["message"], "请求参数校验失败")
        self.assertIsInstance(body["data"], list)

    def test_missing_book_returns_404(self):
        for response in (
            self.client.get("/books/999"),
            self.client.patch("/books/999", json={"stock": 1}),
            self.client.delete("/books/999"),
        ):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], 404)
            self.assertIsNone(response.json()["data"])

    def test_update_rejects_null_fields(self):
        book = self.client.post("/books", json=self._payload()).json()["data"]
        for field in ("title", "price", "stock"):
            response = self.client.patch(f"/books/{book['id']}", json={field: None})
            self.assertEqual(response.status_code, 422, field)
            self.assertIn("不能为 null", response.json()["message"])

    def test_unhandled_exception_returns_unified_500(self):
        client = TestClient(app, raise_server_exceptions=False)
        with patch.object(book_service.BookService, "list_books", side_effect=RuntimeError("boom")):
            response = client.get("/books")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["code"], 500)
        self.assertEqual(response.json()["message"], "服务器内部错误")

    def test_unknown_route_returns_unified_404(self):
        response = self.client.get("/not-exists")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], 404)

    def test_offset_pagination(self):
        self._seed(5)
        first = self.client.get("/books", params={"page": 1, "page_size": 2}).json()["data"]
        self.assertEqual(len(first["items"]), 2)
        self.assertEqual(first["total"], 5)
        self.assertEqual(first["page"], 1)
        self.assertTrue(first["has_more"])
        self.assertIsNone(first["next_cursor"])

        last = self.client.get("/books", params={"page": 3, "page_size": 2}).json()["data"]
        self.assertEqual(len(last["items"]), 1)
        self.assertFalse(last["has_more"])

    def test_cursor_pagination(self):
        self._seed(5)
        first = self.client.get("/books", params={"cursor": "", "page_size": 2}).json()["data"]
        self.assertEqual(len(first["items"]), 2)
        self.assertTrue(first["has_more"])
        self.assertIsNone(first["total"])
        self.assertIsNotNone(first["next_cursor"])

        second = self.client.get(
            "/books", params={"cursor": first["next_cursor"], "page_size": 2}
        ).json()["data"]
        self.assertEqual(len(second["items"]), 2)

        third = self.client.get(
            "/books", params={"cursor": second["next_cursor"], "page_size": 2}
        ).json()["data"]
        self.assertEqual(len(third["items"]), 1)
        self.assertFalse(third["has_more"])
        self.assertIsNone(third["next_cursor"])

    def test_pagination_rejects_both_modes(self):
        response = self.client.get("/books", params={"page": 1, "cursor": 0})
        self.assertEqual(response.status_code, 422)
        self.assertIn("不能同时使用", response.json()["message"])

        empty_cursor = self.client.get("/books", params={"page": 1, "cursor": ""})
        self.assertEqual(empty_cursor.status_code, 200)
        self.assertIsNotNone(empty_cursor.json()["data"]["total"])

    def test_default_cursor_first_page(self):
        self._seed(3)
        by_default = self.client.get("/books", params={"page_size": 2}).json()["data"]
        self.assertIsNone(by_default["total"])
        self.assertEqual(len(by_default["items"]), 2)
        self.assertIsNotNone(by_default["next_cursor"])

        by_empty = self.client.get("/books", params={"cursor": "", "page_size": 2}).json()["data"]
        self.assertEqual(
            [book["id"] for book in by_empty["items"]],
            [book["id"] for book in by_default["items"]],
        )

    def test_keyword_search(self):
        self._seed(5)
        by_title = self.client.get("/books", params={"keyword": "书3", "page": 1}).json()["data"]
        self.assertEqual(by_title["total"], 1)
        self.assertEqual(by_title["items"][0]["title"], "书3")

        by_author = self.client.get("/books", params={"keyword": "Cormen", "page": 1}).json()["data"]
        self.assertEqual(by_author["total"], 5)

        by_isbn = self.client.get(
            "/books", params={"keyword": "9780000000002", "page": 1}
        ).json()["data"]
        self.assertEqual(by_isbn["total"], 1)
        self.assertEqual(by_isbn["items"][0]["title"], "书2")

    def test_exclude_ids(self):
        ids = self._seed(5)
        single = self.client.get(
            "/books", params={"exclude": str(ids[0]), "page": 1}
        ).json()["data"]
        self.assertEqual(single["total"], 4)
        self.assertNotIn(ids[0], [book["id"] for book in single["items"]])

        repeated = self.client.get(
            "/books", params=[("exclude", str(ids[1])), ("exclude", str(ids[2])), ("page", "1")]
        ).json()["data"]
        self.assertEqual(repeated["total"], 3)

        comma = self.client.get(
            "/books", params={"exclude": f"{ids[0]},{ids[1]}", "page": 1}
        ).json()["data"]
        self.assertEqual(comma["total"], 3)

    def test_search_and_exclude_with_pagination(self):
        ids = self._seed(5)
        data = self.client.get(
            "/books",
            params={"keyword": "书", "exclude": str(ids[0]), "page": 1, "page_size": 2},
        ).json()["data"]
        self.assertEqual(data["total"], 4)
        self.assertEqual(len(data["items"]), 2)
        self.assertTrue(data["has_more"])

        cursor_data = self.client.get(
            "/books",
            params={"cursor": "", "page_size": 2, "keyword": "书", "exclude": str(ids[0])},
        ).json()["data"]
        self.assertEqual(len(cursor_data["items"]), 2)
        self.assertNotIn(ids[0], [book["id"] for book in cursor_data["items"]])

    def test_invalid_exclude_returns_422(self):
        response = self.client.get("/books", params={"exclude": "abc"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("exclude", response.json()["message"])

    def test_page_size_out_of_range(self):
        self.assertEqual(self.client.get("/books", params={"page_size": 101}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
