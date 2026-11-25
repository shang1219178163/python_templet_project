"""数据库初始化辅助逻辑测试：旧表改名、旧库补列。"""

import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.db.init import _ensure_schema, _migrate_table_name


def make_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class EnsureSchemaTest(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine()
        with self.engine.begin() as conn:
            conn.execute(text("CREATE TABLE book (id INTEGER PRIMARY KEY, title VARCHAR(100))"))

    def tearDown(self):
        self.engine.dispose()

    def test_adds_publisher_column_idempotently(self):
        _ensure_schema(self.engine)
        columns = {col["name"] for col in inspect(self.engine).get_columns("book")}
        self.assertIn("publisher", columns)

        _ensure_schema(self.engine)  # 第二次执行不应报错


class MigrateTableNameTest(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine()
        with self.engine.begin() as conn:
            conn.execute(text("CREATE TABLE books (id INTEGER PRIMARY KEY, title VARCHAR(100))"))
            conn.execute(text("INSERT INTO books (title) VALUES ('legacy')"))

    def tearDown(self):
        self.engine.dispose()

    def test_renames_legacy_table_idempotently(self):
        _migrate_table_name(self.engine)

        tables = set(inspect(self.engine).get_table_names())
        self.assertIn("book", tables)
        self.assertNotIn("books", tables)

        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT title FROM book")).scalar(), "legacy")

        _migrate_table_name(self.engine)  # 第二次执行不应报错


if __name__ == "__main__":
    unittest.main()
