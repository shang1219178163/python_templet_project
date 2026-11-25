# DTO 模块说明（app/dto）

> 说明：本模块原名 `app/schema`，2026-11-25 已更名为 `app/dto`，类名与职责不变。

## 一、是什么

`app/dto/` 是**接口契约层（DTO 层）**：只放 pydantic 模型，专门定义「接口收什么、返回什么」，不碰数据库。

DTO（Data Transfer Object）就是接口传输对象。它回答两个问题：

- 客户端**能提交**哪些字段、字段格式有什么要求？
- 接口**会返回**哪些字段、序列化成什么样子？

## 二、里面有什么

当前只有 `app/dto/book.py`，包含 4 个类：

| 类 | 角色 | 关键点 |
|---|---|---|
| `BookBase` | 公共字段基类 | 只被继承，不直接使用；统一 `str_strip_whitespace` |
| `BookCreate` | 进模型（POST） | 没有 `id`，`extra="forbid"` 拒绝多余字段 |
| `BookUpdate` | 进模型（PATCH） | 字段全可选，配合 `exclude_unset` 只改提交的字段 |
| `BookOut` | 出模型（响应） | `from_attributes=True` 可从 ORM 转换；价格序列化成两位小数字符串 |

`app/dto/__init__.py` 只是包标记，没有逻辑。

`app/dto/pagination.py` 提供两组模型：`PageQuery` 承载列表查询参数（`keyword` / `exclude` / `page` / `cursor` / `page_size`），
`Page[T]` 只作为分页响应（普通分页带 `total` / `page`，游标分页带 `next_cursor`）。

## 三、在整体链路中的位置

```
HTTP 请求 JSON
    │  FastAPI 用 BookCreate / BookUpdate 校验
    ▼
app/main.py                  ← 创建应用、注册路由与异常处理
    ▼
app/api/routes/book.py       ← 只依赖 DTO 和 service
    ▼
app/db_service/book_service.py  ← BookService：业务规则 + 模型转换
    ▼
app/db/book_table.py         ← ORM 表模型，只在 service 内部出现
    ▼
SQLite data/app.db
    │  查询结果转成 BookOut
    ▼
HTTP 响应 JSON
```

职责边界：

- **api 层**：解析请求、返回响应，只认 DTO。
- **service 层**：业务规则校验，负责 DTO ↔ ORM 的转换。
- **db 层**：表映射与查询，不感知接口。

## 四、和 app/model、app/db 的区别

| 目录 | 内容 | 是否碰数据库 |
|---|---|---|
| `app/dto/` | `BookCreate` / `BookUpdate` / `BookOut` | 否，纯 pydantic |
| `app/model/` | 旧演示用 pydantic 模型（`book.py` 等，被 `app/page/` 使用） | 否 |
| `app/db/` | SQLAlchemy 连接、`BookTable`、初始化脚本、`app.db` | 是 |

三者职责分开，对应 `docs/ORM进模型出模型最佳实践.md` 中「ORM / 进模型 / 出模型」的分层。

## 五、为什么叫 DTO

`dto` 与 `schema`、`contracts`、`api_models` 是同义命名。FastAPI 的 OpenAPI 文档里把请求/响应结构叫 schema，所以早期用了 `schema`；后来按团队习惯改为 `dto`。目录名只是约定，不影响运行。

## 六、以后怎么扩展

每新增一个资源，就在 `app/dto/` 下加一个文件，例如学生模块：

```
app/dto/
  book.py      # BookBase / BookCreate / BookUpdate / BookOut
  student.py   # StudentBase / StudentCreate / StudentUpdate / StudentOut
```

通用约定：

- 进模型不带主键，加 `extra="forbid"`。
- 更新模型字段全可选，服务层用 `exclude_unset=True`。
- 出模型加 `from_attributes=True`，敏感字段不要放进出模型。
