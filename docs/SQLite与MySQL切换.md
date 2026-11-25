# SQLite 与 MySQL 切换

> 适用：本项目（Python 3.13 + FastAPI + SQLAlchemy 2.x）。
> 相关文档：[SQLAlchemy创建数据库.md](./SQLAlchemy创建数据库.md)、[ORM进模型出模型最佳实践.md](./ORM进模型出模型最佳实践.md)。

一个进程只连接一个数据库，连接哪个由 `DATABASE_URL` 决定：不配置时用本地 SQLite，配置后使用对应的 MySQL。
两者共用同一套 ORM、DTO 与 service，切换只改配置，不改代码。

## 一、切换原理（已支持）

核心在 `app/db/__init__.py`：

```python
DATABASE_URL = settings.database_url or f"sqlite:///{DB_FILE}"
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    echo=settings.sql_echo,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_pre_ping=not IS_SQLITE,  # MySQL 长连接取用前先探活
)
```

- **不配** `DATABASE_URL`：使用本地 `data/app.db`（SQLite）。
- **配了** `DATABASE_URL`：使用指定的 MySQL / PostgreSQL。
- `connect_args` 按方言区分，MySQL 不会收到 SQLite 专用参数。
- 非 SQLite 连接启用 `pool_pre_ping`，取连接前先探活。

## 二、切换到 MySQL 的步骤

### 1. 安装驱动（已加入项目依赖）

```bash
uv add pymysql
```

项目当前 `pyproject.toml` 已包含 `pymysql`，新环境执行 `uv sync` 即可。

### 2. 在服务端建库

```sql
CREATE DATABASE bookdb DEFAULT CHARSET utf8mb4;
```

### 3. 配置连接串

本地 `.env`（不提交）或生产环境变量：

```dotenv
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/bookdb?charset=utf8mb4
```

- 密码含 `@`、`/`、`:` 等字符时需要 URL 编码。
- 建议显式带 `charset=utf8mb4`，避免中文和 emoji 乱码。
- 生产环境优先用环境变量注入，不要把密码写进代码或提交 `.env`。

### 4. 重启服务

启动时 `init_db()` 会自动建表并在空库写入示例数据：

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## 三、兼容性检查

| 项目 | 结论 |
|---|---|
| `String` / `Numeric(8,2)` / `func.count()` | SQLite 与 MySQL 都支持 |
| `CheckConstraint("stock <= total_num")` | MySQL **8.0.16+** 才真正强制执行；更早版本忽略，但 service 的 `_check_stock` 已兜底 |
| `unique=True` / `index=True` | 两边都支持 |
| `create_all` | 两边都能建表；正式环境建议用 Alembic 管理变更 |
| 连接池 | MySQL 已启用 `pool_pre_ping`，避免连接被服务端断开后报错 |
| 异步 | 当前是同步 SQLAlchemy（`pymysql`）；要用异步需换 `asyncmy` + `AsyncSession` |
| 默认值 / 自增 | 两边行为一致，`mapped_column(primary_key=True, autoincrement=True)` 可直接用 |

旧库升级：`init_db()` 启动时会先把旧表 `books` 自动改名为 `book`，再检查缺少的 `publisher` 列并执行一次
`ALTER TABLE ... ADD COLUMN publisher ...`（幂等，SQLite 与 MySQL 都支持），无需手工迁移。

## 四、常见问题

**Q：切到 MySQL 后 `data/app.db` 还有用吗？**
没有。它只在未配置 `DATABASE_URL` 时使用；切换后数据不会自动迁移，需要重新播种或用工具导数据。

**Q：SQLite 和 MySQL 的表结构会一致吗？**
会。两边都由同一套 ORM 模型通过 `Base.metadata.create_all()` 生成。但 SQLite 的类型更宽松，MySQL 的约束更严格，切库后建议跑一遍接口测试。

**Q：生产环境还用 `create_all` 吗？**
不建议。`create_all` 不会修改已有表结构，正式项目应改用 Alembic 迁移。
