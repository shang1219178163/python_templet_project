"""数据库初始化辅助逻辑测试：旧库补列。"""

import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.db.init import _ensure_schema


class EnsureSchemaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        with self.engine.begin() as conn:
            conn.execute(text("CREATE TABLE books (id INTEGER PRIMARY KEY, title VARCHAR(100))"))

    def tearDown(self):
        self.engine.dispose()

    def test_adds_publisher_column_idempotently(self):
        _ensure_schema(self.engine)
        columns = {col["name"] for col in inspect(self.engine).get_columns("books")}
        self.assertIn("publisher", columns)

        _ensure_schema(self.engine)  # 第二次执行不应报错


if __name__ == "__main__":
    unittest.main()
