"""图书业务逻辑：业务规则校验、ORM 与进出模型之间的转换。

接口层只依赖这里，不直接操作 ORM 对象。
"""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.book_table import BookTable
from app.dto.book import BookCreate, BookOut, BookUpdate
from app.dto.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page


class BookNotFoundError(Exception):
    """图书不存在"""


class BookConflictError(Exception):
    """违反唯一约束，如 ISBN 已存在"""


class BookRuleError(Exception):
    """违反业务规则，如库存大于总数"""


class BookService:
    """图书业务服务：持有数据库会话，方法不再重复接收 db。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _check_stock(total_num: int, stock: int) -> None:
        if stock > total_num:
            raise BookRuleError(f"库存 {stock} 不能大于总数 {total_num}")

    @staticmethod
    def _to_out(row: BookTable) -> BookOut:
        """ORM 对象 -> 出模型"""
        return BookOut.model_validate(row)

    def list_books(
        self,
        *,
        cursor: int | None = None,
        page: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        keyword: str | None = None,
        exclude: list[str] | None = None,
    ) -> Page[BookOut]:
        """图书列表，同时支持普通分页与游标分页，并可模糊搜索、排除指定 id。

        - 传 `page`：普通分页（OFFSET / LIMIT），结果带 `total` 与 `page`
        - 不传 `page`：游标分页（`id > cursor`），结果带 `next_cursor`；`cursor` 首次传空或不传
        - `page` 与有值的 `cursor` 同时传：抛 `BookRuleError`
        - `keyword`：在书名 / 作者 / ISBN 中模糊匹配
        - `exclude`：排除这些 id，支持重复参数或逗号分隔
        """
        if page is not None and cursor is not None:
            raise BookRuleError("cursor 与 page 不能同时使用")
        if cursor is not None and cursor < 0:
            raise BookRuleError("cursor 必须大于等于 0")
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise BookRuleError(f"page_size 必须在 1 ~ {MAX_PAGE_SIZE} 之间")
        filters = self._build_filters(keyword, exclude)
        if page is not None:
            return self._list_by_page(page, page_size, filters)
        return self._list_by_cursor(cursor or 0, page_size, filters)

    def _build_filters(self, keyword: str | None, exclude: list[str] | None) -> list:
        filters = []
        if keyword:
            escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    BookTable.title.ilike(pattern, escape="\\"),
                    BookTable.author.ilike(pattern, escape="\\"),
                    BookTable.isbn.ilike(pattern, escape="\\"),
                )
            )
        exclude_ids = self._parse_exclude(exclude)
        if exclude_ids:
            filters.append(BookTable.id.not_in(exclude_ids))
        return filters

    @staticmethod
    def _parse_exclude(values: list[str] | None) -> list[int]:
        if not values:
            return []
        ids: list[int] = []
        for value in values:
            for part in value.split(","):
                part = part.strip()
                if not part:
                    continue
                if not part.isdigit():
                    raise BookRuleError(f"exclude 必须是数字 id，收到: {part}")
                ids.append(int(part))
        return ids

    def _list_by_page(self, page: int, page_size: int, filters: list) -> Page[BookOut]:
        """普通分页：返回总数，适合需要页码跳转的场景"""
        if page < 1:
            raise BookRuleError("page 必须大于等于 1")
        offset = (page - 1) * page_size
        total = self.db.scalar(
            select(func.count()).select_from(BookTable).where(*filters)
        ) or 0
        rows = self.db.scalars(
            select(BookTable)
            .where(*filters)
            .order_by(BookTable.id)
            .offset(offset)
            .limit(page_size)
        ).all()
        return Page(
            items=[self._to_out(row) for row in rows],
            page_size=page_size,
            has_more=offset + len(rows) < total,
            total=total,
            page=page,
        )

    def _list_by_cursor(self, cursor: int, page_size: int, filters: list) -> Page[BookOut]:
        """游标分页：按 id 向后翻页，多取一条判断是否还有下一页"""
        rows = self.db.scalars(
            select(BookTable)
            .where(BookTable.id > cursor, *filters)
            .order_by(BookTable.id)
            .limit(page_size + 1)
        ).all()
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        return Page(
            items=[self._to_out(row) for row in rows],
            page_size=page_size,
            has_more=has_more,
            next_cursor=rows[-1].id if has_more else None,
        )

    def count_books(self) -> int:
        return self.db.scalar(select(func.count()).select_from(BookTable)) or 0

    def get_book(self, book_id: int) -> BookOut:
        row = self.db.get(BookTable, book_id)
        if row is None:
            raise BookNotFoundError(f"图书 {book_id} 不存在")
        return self._to_out(row)

    def create_book(self, payload: BookCreate) -> BookOut:
        self._check_stock(payload.total_num, payload.stock)
        row = BookTable(**payload.model_dump())
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise BookConflictError(f"ISBN {payload.isbn} 已存在") from exc
        self.db.refresh(row)
        return self._to_out(row)

    def update_book(self, book_id: int, payload: BookUpdate) -> BookOut:
        row = self.db.get(BookTable, book_id)
        if row is None:
            raise BookNotFoundError(f"图书 {book_id} 不存在")

        # exclude_unset：只取客户端真正提交的字段，未提交的保持原值
        changes = payload.model_dump(exclude_unset=True)
        null_fields = [key for key, value in changes.items() if value is None]
        if null_fields:
            raise BookRuleError(f"更新字段不能为 null: {', '.join(null_fields)}")
        self._check_stock(changes.get("total_num", row.total_num), changes.get("stock", row.stock))
        for key, value in changes.items():
            setattr(row, key, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise BookConflictError("更新后的数据违反数据库约束") from exc
        self.db.refresh(row)
        return self._to_out(row)

    def delete_book(self, book_id: int) -> None:
        row = self.db.get(BookTable, book_id)
        if row is None:
            raise BookNotFoundError(f"图书 {book_id} 不存在")
        self.db.delete(row)
        self.db.commit()
