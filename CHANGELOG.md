# CHANGELOG

## 2026-11-25

### 重构：AI 对话拆分为 app/page/ai_chat 包（21:48）

- `app/page/ai_chat_test.py` 移入 `app/page/ai_chat/`，按职责拆分：
  - `chat.py`：`AIChat`，模型客户端、工具注册表、消息历史与问答循环；
  - `stream.py`：`consume_stream()`，流式分片累积与终端输出；
  - `prompt.py`：`build_system_prompt()`，构造对话时生成，时间不会过期；
  - `main.py`：命令行入口，`python -m app.page.ai_chat.main`；
  - `__init__.py`：导出 `AIChat`。
- `AIChat` 构造函数支持注入 `client` / `mcp`，便于离线测试；新增 `ask()` / `close()`。
- 新增 `tests/test_ai_chat.py`（4 个用例）：工具轮次后回答、第二轮请求包含工具结果、
  直接回答不请求第二轮、工具轮次上限。
- `tests/test_ai_chat_stream.py` 改从 `app.page.ai_chat.stream` 导入。
- 文档：新增 `app/page/ai_chat/README.md`；`app/ai_tool/README.md` 的引用路径同步。
- 验证：全量 128 个测试通过；`python -m app.page.ai_chat.main` 可启动；真实流式请求正常。

### 修复：reasoning_content 先收窄为 str 再拼接（21:43）

- `app/page/ai_chat_test.py`：`reasoning_content` 是 OpenAI SDK 透传的 extra 字段，
  `getattr` 拿到的是任意类型，直接 `append` 到 `list[str]` 会触发类型告警。
  改为 `isinstance(reasoning_text, str)` 收窄后再打印与拼接，非字符串分片直接忽略。
- `tests/test_ai_chat_stream.py` 增加非字符串分片用例，6 个用例全过；全量 124 个测试通过。

### 调整：AI 对话改为流式输出（21:41）

- `app/page/ai_chat_test.py`：`reply()` 的请求改为 `stream=True`，边收边打印。
- 新增 `_consume()`：把分片累积成完整助手消息——`reasoning_content` 与 `content`
  分别拼接，`tool_calls` 按 index 合并 id / name / arguments。思考模式下必须原样
  回传这些字段，否则下一轮带 tools 的请求会 400。
- 终端输出：思考内容以「思考: 」前缀流式打印，正文以「回答: 」前缀流式打印，
  工具调用结果仍单行打印。
- 新增 `tests/test_ai_chat_stream.py`（5 个离线用例）：文本拼接、思考内容保留、
  工具调用分片合并与排序、空 choices 跳过。
- 真实请求验证：普通问答与「查天气 → 工具 → 再回答」两轮均正常，
  思考内容和工具分片都能完整回传。全量 123 个测试通过。

### 修复：工具元数据不再声明为 ClassVar（21:39）

- `app/ai_tool/tool_registry.py`：`BaseTool` 的 `name` / `description` / `parameters`
  由 `ClassVar` 改为普通注解，类属性与实例属性都合法。
- 原因：`MCPTool` 的名字和 schema 由远端 `tools/list` 在运行期决定，只能在 `__init__`
  里赋值；原 `ClassVar` 声明会触发「无法通过实例赋值给类变量」的类型告警。
- 5 个内置工具（天气、搜索、路径规划、火车、OCR）同步去掉 `ClassVar`；
  `MeteoWeatherTool._WEATHER_TEXT` 是真正的类常量，保留 `ClassVar`。
- `app/ai_tool/README.md` 的「新增工具」示例同步调整。
- 全量 118 个测试通过，`app/ai_tool` ruff 零告警。

### 新增：AI 工具支持 MCP（21:33）

- 新增 `app/ai_tool/mcp_tool.py`：MCP 适配层，把 MCP server 上的工具注册进现有 `ToolRegistry`。
  - `MCPServerConfig`：`command`（stdio 子进程）与 `url`（Streamable HTTP）二选一，带 `connect_timeout` / `call_timeout`。
  - `MCPConnection`：每个 server 一个后台线程跑 asyncio 事件循环，同步代码可直接 `call_tool()`；不把对话循环改成 async。
  - `MCPTool`：远程工具代理，名字加 `mcp__{server}__{tool}` 前缀，避免与本地工具重名。
  - `MCPToolManager`：读配置、批量启动、汇总工具；单个 server 失败只记进 `errors`，不影响本地工具。
  - 结果渲染：文本块按行拼接，图片/音频/资源链接给说明，结构化数据仅在文本为空时兜底；`is_error` 抛 `ToolError`。
- 新增 `app/assets/mcp_servers.json`（默认 `{"mcpServers": {}}`，可留空不启用 MCP）。
- `app/page/ai_chat_test.py`：构造时启动 MCP manager，工具注册表追加远程工具；退出时 `close()` 释放连接与子进程。
- `app/ai_tool/__init__.py`：导出 `MCPConnection` / `MCPServerConfig` / `MCPTool` / `MCPToolManager`。
- `pyproject.toml`：新增依赖 `mcp>=2.3.0`（此前只是其他包的传递依赖），`uv.lock` 同步更新。
- 新增 `tests/test_mcp_tool.py`（16 个用例，全部离线）：配置校验、结果渲染、工具路由、配置加载，以及进程内 server 的线程桥接；另用真实 stdio 子进程手工验证连接、调用与退出。
- 文档：`app/ai_tool/README.md` 增加「MCP 工具」章节与配置说明。

### 调整：种子文件改名 book.json，表名 books → book（14:08）

- `app/assets/json/books.json` 重命名为 `app/assets/json/book.json`；
  `app/db/init.py` 的 `BOOKS_JSON` 与 `app/model/book_library.py` 的默认路径同步更新。
- `app/db/book_table.py`：`__tablename__` 由 `books` 改为 `book`。
- `app/db/init.py`：新增 `_migrate_table_name()`，启动时把旧库的 `books` 表幂等改名为 `book`；
  `_ensure_schema()` 的补列逻辑改用 `book`。
- 两个数据库已实际迁移并保留数据：
  - SQLite `data/app.db`：`books` → `book`，100 行；
  - MySQL `app`：`books` → `book`，100 行；`user` 101 行不变。
- 测试：`tests/test_db_init.py` 增加旧表改名用例，全量 102 个测试通过。
- 文档同步：README、ORM/DTO 文档、SQLAlchemy 建库文档、SQLite/MySQL 切换文档中的文件名与表名。
- 说明：接口路径仍为 `/books`，本次只改数据文件与数据库表名。

### 清理：删除未使用的 app/util/file_ext.py（14:02）

- 全仓库无引用（`file_ext` / `FileExt` 均无导入），删除后 `app.util` 导入正常。
- 全量 101 个测试通过。
- 删除已暂存，尚未提交。

### 清理：删除 PageQuery 的 keyword 空值校验器（13:56）

- `app/dto/pagination.py`：移除 `_blank_keyword_to_none`。`str_strip_whitespace` 已把空格处理为空串，
  而 `_build_filters` 用 `if keyword` 判断，空串本来就不会加过滤条件，行为不变。
- 保留 `_empty_cursor_to_none`：`cursor` 是 `int | None`，空字符串若不转 `None` 会在 `int_parsing` 阶段 422，
  「首次传空」将不可用。
- 验证：`keyword=` 与 `keyword='   '` 都返回全部 100 条；`keyword=算法` 命中 1 条；
  `?cursor=` 仍返回游标首页。全量 101 个测试通过，`pagination.py` ruff 零告警。

### 调整：不传 page 时默认走游标分页，cursor 首页可不传或传空（13:54）

- `app/dto/pagination.py`：`page` 说明改为「不传则走游标分页」；`cursor` 说明改为「首次传空或不传」；
  移除 `use_cursor` 属性，空 `cursor=` 统一转为 `None`。
- `app/db_service/book_service.py`：分页模式改为——传 `page` 走普通分页；不传 `page` 一律走游标分页
  （`cursor` 为空按 0 处理）；只有 `page` 与有值的 `cursor` 同时传才抛 422。
- `app/api/routes/book.py`：移除 `use_cursor` 传参。
- 行为变化：`GET /books` 不再默认普通分页，默认返回游标首页（`total=null`）；需要 `total` 时显式传 `page=1`。
- 测试：新增「默认游标首页」用例；搜索/排除断言补充 `page=1`；空 cursor + page 改为合法（走普通分页）；
  全量 101 个测试通过。
- 文档：`README.md`、`docs/ORM进模型出模型最佳实践.md` 更新分页默认行为与示例。
- 验证：默认 / `?cursor=` / `?cursor=0` 均为游标首页；`?page=1` 返回 `total=100`；
  `?page=1&cursor=0` 返回 422；本次改动文件 ruff 零告警。

### 调整：游标分页首次传空 `cursor=`（13:53）

- `app/dto/pagination.py`：`cursor` 说明改为「上一页最后一条 id；首次传空」；
  新增 `mode="before"` 校验器把 `?cursor=` 转为 `None`，并用 `model_fields_set` 区分
  「显式传空」与「完全不传」；新增 `use_cursor` 属性。
- `app/db_service/book_service.py`：`list_books` 新增 `use_cursor` 参数；显式传 cursor（含空值）走游标分页，
  空值按 0 处理从第一条开始；仍校验 `cursor` 非负、与 `page` 互斥。
- `app/api/routes/book.py`：把 `query.use_cursor` 传给 service。
- 测试：游标分页首次请求改为 `cursor=""`；新增「空 cursor + page → 422」断言；全量 100 个测试通过。
- 文档：`README.md`、`docs/ORM进模型出模型最佳实践.md` 改为首次传空。
- 验证：`?cursor=&page_size=2` 返回游标首页（total=null，next_cursor 正常）；`?cursor=0` 仍可用；
  不传 cursor 仍走普通分页（total=100）；`?cursor=&page=1` 返回 422；本次改动文件 ruff 零告警。

### 调整：模糊搜索仅覆盖书名、作者、ISBN（13:50）

- `app/db_service/book_service.py`：`_build_filters()` 的 OR 条件移除 `publisher`，只保留
  `title` / `author` / `isbn` 的 `ILIKE` 匹配。
- `app/dto/pagination.py`：`PageQuery.keyword` 的字段说明与类文档同步改为「书名 / 作者 / ISBN」。
- `tests/test_book_api.py`：关键词用例改为分别验证书名、作者、ISBN；不再断言出版社可搜索。
- 文档同步：`README.md`、`docs/ORM进模型出模型最佳实践.md`。
- 验证：`keyword=算法`、`keyword=Cormen`、`keyword=9787111000013` 均命中《算法导论》；
  `keyword=机械工业` 返回 0；全量 100 个测试通过，本次改动文件 ruff 零告警。
- 说明：`publisher` 仍保留在数据、ORM 和接口响应中，只是不参与模糊搜索。

### 功能：图书列表支持模糊搜索与 exclude 排除（13:44）

- `app/dto/pagination.py`：新增 `PageQuery` 查询模型，包含：
  - `keyword: str | None`（最长 100，空串转 None）
  - `exclude: list[str]`（默认空列表，支持重复参数或逗号分隔）
  - `page` / `cursor` / `page_size`；`Page[T]` 仍只作为响应模型。
- `app/api/deps.py`：新增 `PageQueryDep = Annotated[PageQuery, Query()]`，路由以查询参数模型接收。
- `app/api/routes/book.py`：`GET /books` 改为接收 `PageQuery`，把 keyword/exclude 传给 service。
- `app/db_service/book_service.py`：
  - 模糊搜索覆盖 `title` / `author` / `publisher` / `isbn`，使用 `ILIKE`，并转义 `%`、`_`；
  - `exclude` 解析为 id 列表，非数字抛 `BookRuleError`（422）；
  - offset 分页的 `total` 为过滤后的数量，游标分页同样应用过滤条件。
- 测试：新增关键词搜索、exclude（单个/重复/逗号）、搜索+排除+分页/游标、非法 exclude 4 组用例；
  全量 100 个测试通过。
- 验证：真实接口 `keyword=算法` 命中 1 本，`keyword=机械工业&exclude=204` 正常，`exclude=abc` 返回 422，
  `/openapi.json` 200；本次改动文件 ruff 零告警。
- 文档同步：`README.md`、`docs/ORM进模型出模型最佳实践.md`、`docs/DTO模块说明.md`。

### 修复：代码审核发现的 7 个问题（13:39）

- **PATCH 显式 null**：`BookService.update_book` 在 `exclude_unset` 后检查值为 `None` 的字段，
  抛 `BookRuleError` 返回 422；避免 `stock=null` 触发 `TypeError` 变 500、`title=null` 写入 NOT NULL 列变 409。
- **旧库补列**：`app/db/init.py` 新增 `_ensure_schema()`，启动时检查 `books` 是否缺少 `publisher` 列，
  缺失则执行幂等 `ALTER TABLE`；并发启动时若其他进程已加列则忽略异常。
- **兜底异常**：`app/api/errors.py` 注册 `Exception` 处理器，未预期异常统一返回
  `ApiResponse(code=500, message="服务器内部错误")`，并记录 `logger.exception` 堆栈。
- **播种并发**：`_seed()` 捕获 `IntegrityError` 后回滚，避免多 worker 冷启动时后提交者因 ISBN 唯一约束启动失败。
- **惰性加载**：移除模块级 `SEED_BOOKS = load_seed_books()`，改为 `_seed()` 内按需读取 JSON；
  导入 `app.main` 不再触发文件 IO，JSON 缺失也不会导致测试收集失败。
- **入口端口**：`app/main.py` 直接运行时改为 `uvicorn.run("app.main:app", port=8001, reload=True)`，
  与 README/docstring 一致并恢复热重载。
- **调试文档**：`docs/后端调试指南.md` 两处 `app.api.book:app` 改为 `app.main:app`。
- 测试：新增 `test_update_rejects_null_fields`、`test_unhandled_exception_returns_unified_500`、
  `tests/test_db_init.py`（补列幂等）；全量 96 个测试通过。
- 验证：真实接口三组 `PATCH null` 均返回 422；`python -m app.main` 监听 8001 且 reloader 正常；
  本次改动文件 ruff 零告警。审核中的 `/slow` 演示端点与 `db.refresh` 优化（第 8、9 项）按要求暂未处理。

### 功能：出版社字段接入 ORM/DTO，并同步 SQLite 与 MySQL（13:25）

- `app/db/book_table.py`：`BookTable` 新增 `publisher` 列（`String(100)`，默认空字符串）。
- `app/dto/book.py`：`BookBase` 新增 `publisher`（创建/响应共用），`BookUpdate` 新增可选的 `publisher`。
- `app/db/init.py`：`load_seed_books()` 从 JSON 读取 `publisher`，种子数据写入时一并落库。
- 两个数据库均执行 `ALTER TABLE books ADD COLUMN publisher VARCHAR(100) NOT NULL DEFAULT ''`，
  再按 ISBN 同步 `books.json` 的 100 条数据：
  - SQLite `data/app.db`：新增 97 本、更新 3 本，共 100 本，ISBN 100 个不重复；
  - MySQL `app.books`：新增 97 本、更新 3 本，共 100 本；`app.user` 101 行不变。
- 接口 `BookOut` 现在会返回 `publisher`，已验证 `/books?page_size=3` 返回出版社与价格。
- `tests/test_book_api.py`：创建用例补充 `publisher` 字段并断言返回。
- 验证：接口测试 11 个、全量 93 个测试通过；本次改动文件 ruff 零告警。

### 数据：books.json 增加出版社字段（13:24）

- `app/assets/json/books.json`：100 条书目全部新增 `publisher` 字段，共涉及 24 家出版社；
  字段顺序调整为 `title` / `author` / `publisher` / `isbn` / `price` / `total_num` / `stock` / `industry`。
- 出版社信息与定价对应的常见版次一致，例如算法导论/深入理解计算机系统为机械工业出版社，
  机器学习/人工智能为清华大学出版社，医学类为人民卫生出版社。
- `app/db/init.py` 的 `load_seed_books()` 仍只提取 ORM 需要的字段，`publisher` 暂不写入数据库
  （`BookTable` 当前没有该列）。
- `README.md` 数据源字段说明补充 `publisher`。
- 验证：JSON 100 条全部匹配、无缺失；种子加载 100 条正常；全量 93 个测试通过；`init.py` ruff 零告警。

### 数据：books.json 的价格替换为真实定价（13:23）

- `app/assets/json/books.json`：100 条书目的 `price` 全部替换为公开渠道查到的官方定价（常见版次），
  价格范围 13.60 ~ 208.00 元。原按序号生成的 10.90 ~ 99.90 演示价格已全部移除。
- 来源类型：高等教育出版社、人民卫生出版社、清华大学出版社、北京大学出版社、机械工业出版社等出版社页面，
  以及全国大中专教材网络采选系统、当当/文轩等商品页的“定价”字段。
- 同步 MySQL `app.books` 现有 3 本的 `price`：算法导论 128.00、计算机程序设计艺术 98.00、深入理解计算机系统 139.00；
  `user` 表 101 行不变。
- 重要说明：`books.json` 中的 ISBN 仍是原文件按规律生成的值，并非真实版次；本次价格对应的是“书名 + 常见版次”，
  不是该 ISBN 指向的版本。若要求 ISBN 与价格严格对应，需要同时替换 ISBN。
- 验证：`load_seed_books()` 读取 100 条，`price` 均为 `Decimal` 且大于 0；内存 SQLite 写入 100 行成功；
  全量 93 个测试通过；`app/db/init.py` ruff 零告警。
- `README.md` 补充说明：价格为常见版次官方定价，版次/印次不同会有差异。

### 数据：books.json 增补价格与库存字段并作为种子数据源（13:18）

- `app/assets/json/books.json`：100 条书目全部补充 `price` / `total_num` / `stock` 字段；
  前 3 条沿用原 `SEED_BOOKS` 的值（66.00/5/5、77.00/3/3、88.00/4/4），其余按序号生成演示值；
  保留原有 `industry` 字段。
- `app/db/init.py`：新增 `load_seed_books()`，从 `app/assets/json/books.json` 读取种子数据；
  `SEED_BOOKS` 由该函数生成，价格转 `Decimal`、库存与总数为 `int`；空库时播种 100 本。
- 验证：内存 SQLite 写入 100 行成功，ISBN 全部唯一；全量 93 个测试通过；`init.py` ruff 零告警。
- 数据库未变：MySQL `app.books` 仍为 3 本（`init_db()` 只在空库时播种）。
  如需按新数据源重播，清空 `books` 后执行 `uv run python -m app.db.init`。

### 数据：MySQL books 表恢复为最初的 3 本示例书（13:16）

- 清空 MySQL `app.books` 的 100 行真实书目，执行 `uv run python -m app.db.init` 重新播种最初的 3 本示例书。
- `app.user` 101 行未受影响。
- 接口验证：`/books/count` 返回 3，`/books` 返回算法导论、计算机程序设计艺术、深入理解计算机系统。
- 说明：自增 id 因历史插入从 204 开始，不影响功能。

### 回退：init.py 恢复为最初的 3 本示例书版本（13:15）

- 使用 git 暂存区版本恢复 `app/db/init.py`：只保留最初的 3 本示例书，`init_db()` 不再包含 `--sync` / `--reset`。
- 删除不再被引用的 `app/db/seed_books.py` 和 `tests/test_seed_books.py`。
- `README.md`、`docs/ORM进模型出模型最佳实践.md` 中的相关说明同步回退。
- 数据库未回退：MySQL `app.books` 仍是 100 本真实图书，`app.user` 仍为 101 行。
  如需让库回到 3 本示例书，可清空 `books` 后重新初始化（会删除现有 100 条书目）：
  `DELETE FROM books;`，再执行 `uv run python -m app.db.init`。
- 验证：全量 93 个测试通过，`app/db/init.py` ruff 零告警，仓库内无 `seed_books` / `--sync` / `--reset` 残留引用。

### 数据：种子图书替换为 100 本真实书目（13:12）

- 新增 `app/db/seed_books.py`：保存 100 本真实图书的（标题, 作者, ISBN-13）。
  书目信息通过公开图书目录与榜单检索获得（Goodreads / goodbooks-10k、出版社在售版本、图书馆书目、
  Scribd Top 50 经典书单等）；ISBN 对应具体版本，同一本书不同出版社可能不同。
- `app/db/init.py`：改为从 `SEED_BOOK_DATA` 生成 `SEED_BOOKS`；价格与库存为演示值；
  新增 `--reset` 清空 `books` 表后重新播种（只影响 `books`，不影响 `user` 等其他表），保留 `--sync`。
- `tests/test_seed_books.py`：4 个用例，校验 100 本、ISBN 唯一且校验位正确、无占位标题、库存不超过总数。
- 已对 MySQL `app` 库执行 `--reset`：删除 100 行旧种子数据，写入 100 本真实图书；
  `user` 表 101 行未受影响，库中无「示例图书」残留。
- 验证：全量 97 个测试通过；`/books/count` 返回 100，分页接口返回真实书名、作者与 ISBN。
- 备注：`app/assets/json/books.json`（旧演示页数据）本次未改动。

### 功能：SEED_BOOKS 扩充到 100 并同步数据库（13:06）

- `app/db/init.py`：新增 `SEED_BOOK_COUNT = 100`，保留 3 本手写示例，其余 97 本由 `_build_seed_books()` 生成
  （标题/作者按序号、ISBN 为 `978` + 10 位数字、价格与库存循环取值），共 100 本且 ISBN 唯一。
- `init_db(sync=False)`：默认仍只在空库时播种；新增 `--sync` 参数，按 ISBN 补齐缺失的示例图书，
  不修改、不删除已有数据，可重复执行。
- 新增 `tests/test_seed_books.py`：校验数量为 100、ISBN 唯一且为 13 位数字、库存不超过总数，3 个用例通过。
- 已对 MySQL `app` 库执行 `--sync`：补充 97 本，`books` 共 100 行、ISBN 100 个不重复，`user` 仍为 101 行；
  再次执行补充 0 本，幂等正常。
- 接口验证：`/books/count` 返回 100；默认分页 20 条、total=100、has_more=true；第 5 页 20 条；
  游标分页连续翻页正常。
- `README.md` 补充 `--sync` 用法；全量 96 个测试通过，本次改动文件 ruff 零告警。

### 调整：MySQL 数据库 bookdb 合并进 app（13:03）

- 现状：`app` 库已有 `user` 表 101 行，`bookdb` 库有 `books` 表 3 行，直接改名会冲突。
- 采用合并方案：`RENAME TABLE bookdb.books TO app.books`，`app.user` 101 行保持不变；确认 `bookdb` 为空后删除该库。
- `.env` 的 `DATABASE_URL` 库名由 `bookdb` 改为 `app`（`.env` 已在 `.gitignore` 中，凭据未写入文档）。
- 验证：`init_db()` 幂等；`/books/count` 返回 3；普通分页与游标分页正常；新增、删除接口可用；
  直连 MySQL 确认最终 `app.books` 3 行、`app.user` 101 行。现有数据库为 `app`、`information_schema`、`mysql`、`performance_schema`、`sys`。

### 验证：MySQL 完整链路（13:00）

- 本机 MySQL 26.7.0，`root@localhost` 认证成功；新建数据库 `bookdb`（utf8mb4），未触碰已有 `app` 库。
- 通过 `DATABASE_URL` 切换到 MySQL，`init_db()` 建表并播种 3 条示例数据；重复执行保持 3 条，幂等正常。
- 接口验证全部通过：默认列表、普通分页（page/page_size）、游标分页（cursor/page_size）、新增、局部更新、
  单条查询、删除、count，以及 404 / 422 / 409 统一错误响应。
- 通过 pymysql 直接回查确认新增、更新、删除均真实落库，最终行数回到 3。
- 表结构：InnoDB / utf8mb4，`isbn` 唯一索引，`stock >= 0` 与 `stock <= total_num` 两条 CHECK 约束生效。
- 凭据未写入代码、文档或 `.env`；临时启动脚本与进程已清理。`bookdb` 暂时保留，可用 `DROP DATABASE bookdb;` 删除。

### 文档：MySQL 支持文档收敛为「按环境切换」范围（12:56）

- `docs/SQLite与MySQL双支持.md` 更名为 `docs/SQLite与MySQL切换.md`。
- 删除「同一进程同时连接两个库」的章节与方案对比；文档明确一个进程只连一个库，由 `DATABASE_URL` 决定。
- `README.md`、`docs/SQLAlchemy创建数据库.md` 的链接与表述同步更新。
- 代码、依赖与测试无变化。

### 功能：支持 SQLite / MySQL 切换，安装 pymysql 并启用 pool_pre_ping（12:55）

- 依赖：`pyproject.toml` / `uv.lock` 新增 `pymysql`，可通过 `DATABASE_URL` 切换到 MySQL。
- `app/db/__init__.py`：新增 `IS_SQLITE` 判断；`connect_args` 仅 SQLite 传 `check_same_thread`；
  非 SQLite 启用 `pool_pre_ping=True`，避免 MySQL 长连接被服务端断开后报错。
- 新增 `docs/SQLite与MySQL双支持.md`：说明「按环境切换」与「同时连两个库」的区别、切换步骤、兼容性检查
  （CHECK 约束需 MySQL 8.0.16+ 等）、多数据源方案对比与常见问题。
- `README.md` 增加 MySQL 切换配置示例；`docs/SQLAlchemy创建数据库.md` 第七节改为通过 `.env` / `DATABASE_URL`
  配置，并补充 utf8mb4、驱动与 `pool_pre_ping` 说明。
- 验证：SQLite 默认 `pre_ping=False`；模拟 `DATABASE_URL=mysql+pymysql://...` 时 dialect 为 `mysql`、驱动 `pymysql`、
  `pre_ping=True`；93 个单元测试通过；本次改动文件 ruff 零告警；真实 uvicorn 启动 `/books/count` 正常。
  未实际连接 MySQL 服务端（本机无实例）。「同一进程同时连两个库」未实现，方案见新文档第五节。

### 功能：图书列表支持普通分页与游标分页（12:48）

- 新增 `app/dto/pagination.py`：通用分页结果 `Page[T]`（`items` / `page_size` / `has_more`，
  普通分页带 `total` / `page`，游标分页带 `next_cursor`），以及 `DEFAULT_PAGE_SIZE=20`、`MAX_PAGE_SIZE=100`。
- `BookService.list_books` 改为关键字参数 `cursor` / `page` / `page_size`，同时支持两种模式：
  - `page`：OFFSET / LIMIT 普通分页，返回 `total` / `page` / `has_more`；
  - `cursor`：`id > cursor` 游标分页，多取一条判断 `has_more` 并返回 `next_cursor`，首次传 `cursor=0`；
  - 两者同时传抛 `BookRuleError`（422）；`page_size` 超出 1~100 也抛 `BookRuleError`。
- `GET /books` 新增查询参数 `page` / `cursor` / `page_size`，响应改为 `ApiResponse[Page[BookOut]]`。
- 测试：新增普通分页、游标分页、两种模式互斥、`page_size` 越界 4 个用例；`test_crud` 适配 `data.items`；
  接口测试共 11 个，全量 93 个测试通过。
- 文档同步：`README.md` 补充分页示例；`docs/ORM进模型出模型最佳实践.md` 更新接口表、目录树与分页说明；
  `docs/DTO模块说明.md` 补充 `pagination.py`。
- 验证：本次改动文件 ruff 零告警；真实请求 `?page=1&page_size=2` 返回 `total=3`，`?cursor=0&page_size=2`
  返回 `next_cursor=2`，两种模式同传返回 422。

### 重构：BookService 方法收进类，路由改用依赖注入（12:37）

- `app/db_service/book_service.py`：模块级函数改为 `BookService` 类，`db` 由 `__init__` 注入；
  `list_books` / `count_books` / `get_book` / `create_book` / `update_book` / `delete_book` 变为实例方法，
  `_check_stock` / `_to_out` 变为静态方法。异常类（`BookNotFoundError` / `BookConflictError` / `BookRuleError`）保持模块级，
  `app/api/errors.py` 无需改动。
- 新增 `app/api/deps.py`：`get_book_service` 用请求级 `Session` 构造 `BookService`，并导出类型别名 `BookServiceDep`。
- `app/api/routes/book.py`：移除 `Session` / `get_db` / `book_service` 导入，端点统一用 `service: BookServiceDep` 调用实例方法。
- 文档同步：`docs/ORM进模型出模型最佳实践.md` 的服务层示例、目录树与接口示例改为类式写法；
  `docs/DTO模块说明.md` 的链路路径更新为 `app/db_service/book_service.py`。
- 验证：89 个单元测试通过；本次改动文件 ruff 零告警；真实 uvicorn 启动 `/books/count` 正常，`/books/999` 返回统一 404。

### 重构：应用入口与路由分离、数据文件移出包、统一错误响应（12:31）

- **P0 应用与路由分离**：新增 `app/api/routes/book.py`（`APIRouter`），删除 `app/api/book.py`；
  `app/main.py` 改为创建 `FastAPI`、注册 lifespan、`include_router` 与异常处理器。启动命令改为 `uvicorn app.main:app`。
- **P1 数据文件移出代码包**：`app/db/app.db` → `data/app.db`；`app/db/__init__.py` 的 `DB_DIR` 改为项目根目录 `data/`，
  默认 SQLite 模式下自动创建目录。`.gitignore` 的 `app.db` 规则仍可跨目录匹配。
- **统一错误响应**：新增 `app/api/errors.py`，把 `HTTPException`、`RequestValidationError` 与业务异常
  （`BookNotFoundError` / `BookConflictError` / `BookRuleError`）统一包装成 `ApiResponse`（`code` / `message` / `data`）。
  路由层移除 `try/except` 与 `_http_error`，业务异常只负责语义，不再关心 HTTP 状态码。
- 修正 `/slow` 的响应类型为 `dict[str, float | int]`（耗时是浮点数，原声明为 `int`）；函数名 `asyncTest` 改为 `async_test`。
- `tests/test_book_api.py`：导入改为 `app.main`；新增未知路由统一 404 用例；补充 404/409/422 响应结构断言，共 7 个用例。
- 文档同步：`README.md`、`docs/SQLAlchemy创建数据库.md`、`docs/ORM进模型出模型最佳实践.md`、
  `docs/DTO模块说明.md`、`docs/后端调试指南.md`、`docs/Pydantic后端必备.md` 更新启动命令、目录结构与数据文件路径。
- 验证：89 个单元测试通过；本次改动文件 ruff 零告警；真实 uvicorn 启动后 `/books/count` 正常，
  `/books/999` 与未知路由均返回 `{"code":404,"message":...,"data":null}`。

### 文档：新增 DTO 模块说明（12:26）

- 新增 `docs/DTO模块说明.md`：解释 `app/dto/` 的定位（接口契约层）、4 个模型的职责、在请求链路中的位置、
  与 `app/model`、`app/db` 的区别、命名由来及后续扩展约定；注明该目录原名 `app/schema`。

### 调整：接口进出模型目录 app/schema 改名为 app/dto（12:25）

- 目录 `app/schema/` → `app/dto/`，模块名改为 `app.dto.book`；类名与职责不变（`BookBase` / `BookCreate` / `BookUpdate` /
  `BookOut`）。
- 同步更新导入：`app/api/book.py`、`app/db_service`。
- `docs/ORM进模型出模型最佳实践.md` 中的路径、目录树与「接口层只碰 DTO」表述同步更新。
- 清理旧包残留的 `app/dto/__pycache__`。
- 验证：`import app.api.book` 正常；88 个单元测试通过；本次改动文件 ruff 零告警；
  真实 uvicorn 启动 `GET /books/1` 返回图书详情正常。

### 调整：数据库相关文件统一收进 app/db 目录（12:20）

- `app/db.py` → `app/db/__init__.py`（改为包，engine / SessionLocal / Base / get_db 位置不变，`from app.db import ...`
  仍可用）；
  `DB_DIR` 改为包所在目录，不再需要 `mkdir`。
- `app/db_init.py` → `app/db/init.py`，手动初始化命令改为 `uv run python -m app.db.init`。
- `app/model/book_table.py` → `app/db/book_table.py`。
- `app/storage/app.db` → `app/db/app.db`，3 条示例数据保留。
- `app/storage/file_ext.py` → `app/util/file_ext.py`（通用 JSON 文件工具，与数据库无关，无代码引用），随后删除空的
  `app/storage`。
- 同步更新导入：`app/api/book.py`（`from app.db.init import init_db`）、`app/db_service`、`tests/test_book_api.py`。
- `README.md`、`app/config.py` 注释、`docs/SQLAlchemy创建数据库.md`、`docs/ORM进模型出模型最佳实践.md` 中的路径与命令同步更新。
- `.gitignore` 移除已失效的 `app/storage/identifier.sqlite` 规则；`app.db` 规则仍可跨目录匹配 `app/db/app.db`。
- 验证：`DATABASE_URL` 指向 `app/db/app.db`；`python -m app.db.init` 幂等（仍为 3 条）；88 个单元测试通过；
  真实 uvicorn 启动 `/books/count` 返回 3、`/docs` 200；本次改动文件 ruff 零告警。

### 调整：SQLite 库文件迁移到 app/storage（12:14）

- `app/db.py`：`DB_FILE` 由「项目根目录 / app.db」改为「`app/storage/app.db`」，默认路径下首次导入自动创建 `storage` 目录（
  `DB_DIR.mkdir`）。
- 现有 `app.db` 已移动到 `app/storage/app.db`，原有 3 条示例图书数据保留。
- `.gitignore` 的 `app.db` 规则可跨目录匹配，`app/storage/app.db` 已被忽略，无需新增规则。
- `README.md`、`app/config.py` 注释、`docs/SQLAlchemy创建数据库.md` 中的路径引用同步更新。
- 验证：`DATABASE_URL` 输出新路径；`python -m app.db_init` 幂等（仍为 3 条）；88 个单元测试通过；本次改动文件 ruff 零告警。

### 清理：移除 PyCharm 生成的 identifier.sqlite（12:09）

- 删除未跟踪文件 `app/storage/identifier.sqlite`：这是 PyCharm Database 面板生成的 SQLite 数据源缓存（内含 `student`
  表），无代码引用。
- `.gitignore` 新增 `app/storage/identifier.sqlite`，避免以后误提交。
- 注意：PyCharm 的 Database 数据源仍在的话，该文件可能被重新生成；如需彻底避免，请在 Database 面板删除对应数据源。

### 功能：图书接口接入 SQLite 数据库，落地 ORM 进出模型分层（12:08）

- 依赖：`pyproject.toml` / `uv.lock` 新增 `sqlalchemy>=2.1.9`。
- 新增 `app/db.py`：engine（SQLite 默认落项目根目录 `app.db`）、`SessionLocal`、`Base`、`get_db` 依赖；
  连接串可用 `DATABASE_URL` 覆盖，SQL 回显用 `SQL_ECHO`。
- 新增 `app/model/book_table.py`：ORM 表模型 `BookTable`，带库存非负、库存不超总数的 `CheckConstraint`，ISBN 唯一索引。
- 新增 `app/schema/book.py`：`BookBase` / `BookCreate` / `BookUpdate` / `BookOut` 分层模型。
  `BookCreate` 不接收 `id` 且 `extra="forbid"`；`BookUpdate` 全可选，配合 `exclude_unset`；
  `BookOut` 加 `from_attributes=True`，价格按两位小数字符串输出。
- 新增 `app/db_service`：列表 / 计数 / 详情 / 新增 / 更新 / 删除，集中做 ORM 与进出模型转换与业务规则校验；
  ISBN 冲突抛 `BookConflictError`，库存大于总数抛 `BookRuleError`。
- 新增 `app/db_init.py`：建表并在空库时写入 3 本示例书，可重复执行；`uv run python -m app.db_init` 手动初始化。
- `app/api/book.py`：新增 `GET /books/{id}`、`POST /books`、`PATCH /books/{id}`、`DELETE /books/{id}`；
  `GET /books` 与 `GET /books/count` 改为真实读库；lifespan 启动时自动建表并播种。
  修正导入 `from api.api_response` → `from app.api.api_response`，从项目根目录启动不再报 `No module named 'api'`。
- 新增 `tests/test_book_api.py`：使用内存 SQLite 覆盖 CRUD、客户端传 id 被拒、ISBN 冲突 409、
  库存超总数 422、ISBN 格式 422、图书不存在 404，共 6 个用例全部通过。
- 新增 `docs/ORM进模型出模型最佳实践.md`：说明 ORM / 进模型 / 出模型的分层、转换位置、校验归属与常见坑。
- `README.md` 更新接口列表、数据库初始化方式与文档入口；`.gitignore` 忽略 `app.db`。
- 验证：`uv run python -m unittest tests.test_book_api -v` 6 个用例通过；
  真实启动 lifespan 后 `/books` 返回 3 本示例书，新增 / 更新 / 删除接口冒烟通过；ruff 零告警。

## 2026-11-24

### 文档：新增数据库创建指南（21:06）

- 新增 `docs/SQLAlchemy创建数据库.md`：说明 SQLite + SQLAlchemy 2.0 的建库建表流程——安装依赖、`app/db.py`
  （engine/session/Base）、ORM 表模型、初始化脚本、FastAPI 依赖注入，以及 PyCharm 连接与命令行查看方式。
- 附 MySQL / PostgreSQL 切换方式与连接串示例；说明 pydantic 模型需 `from_attributes=True` 才能从 ORM 对象转换。
- 内容基于当前项目现状编写：尚无数据库层，`/books` 仍为内存假数据。

### 文档：校对 AI 工具模块 README 表述（19:39）

- `app/ai_tool/README.md`：火车日期说明改为「支持 ISO 8601 日期（含 `20261127` 等变体），无法解析时报格式错误」，与
  `date.fromisoformat()` 的实际行为一致。
- `app/ai_tool/README.md`：明确 `total` 是应用 `train_code` 过滤后、`limit` 截断前的车次数；补充 `duration_min` 为四舍五入取整。
- `app/ai_tool/README.md`：`name` 唯一性限定为「同一个 `ToolRegistry` 内」；测试命令前补充「先激活项目虚拟环境」。

### 功能：新增图片 OCR 文字识别工具（16:59）

- 新增 `app/ai_tool/ocr_tool.py`：`OcrTool`（调用名 `ocr_image`），参数 `image_path`（本地图片路径）。
- 识别引擎优先 `ocrmac`（Apple Vision，`accurate` 级别，中文简体 + 英文），
  未安装、抛异常或识别结果为空时自动回退 `natocr`；返回 JSON 含 `engine` / `text` / `lines`。
- 路径不存在、参数缺失返回中文提示；两个引擎都不可用时抛 `ToolError`；
  图片无文字时返回「图片中没有识别到文字」。
- 依赖：`pyproject.toml` / `uv.lock` 新增 `ocrmac>=1.0.1`、`natocr>=2.3.0`。
- `__init__.py` 导出 `OcrTool`；`app/page/ai_chat_test.py` 注册并补充系统提示。
- `tests/test_ai_tool.py` 新增 8 个离线用例（优先 ocrmac、异常/缺包/空结果回退、双引擎不可用、
  文件不存在不发调用、缺参数），共 58 个测试全部通过。
- `README.md` 更新目录结构、快速用法、内置工具表与 OCR 说明。
- 验证：ruff 零告警；真实识别中英文测试图，`ocrmac` 与强制回退 `natocr` 均返回正确文本。

### 功能：新增中国火车信息查询工具（16:33）

- 新增 `app/ai_tool/train_tool.py`，对接 12306 官方接口，无需密钥。
- `TrainQueryTool`（`query_train`）：按出发站、到达站和日期查询余票与车次时刻，
  返回车次、发到时间、历时、是否可订及各席别余票；支持 `train_code` 指定车次、`limit` 限制条数。
- `TrainStopsTool`（`query_train_stops`）：按区间和车次查询全程经停站、到发时刻与停站时长。
- 站名解析复用 `station_name.js`：兼容「北京南」「北京南站」两种写法；找不到时返回相近车站候选。
- 日期缺省为今天；过去日期与非法格式在本地直接拒绝，不发起网络请求。
- `NetClient` 改用 `build_opener` + `CookieJar`：12306 要求先访问初始化页取得会话，
  之前无状态请求会被跳到错误页；其余工具行为不变。
- `__init__.py` 导出两个新工具；`app/page/ai_chat_test.py` 注册并补充系统提示。
- `tests/test_ai_tool.py` 新增 18 个离线用例（余票解析、区域接口跳转、车次筛选/截断、站名别名与候选、
  日期校验、接口异常、经停站解析等），共 50 个测试全部通过。
- `README.md` 更新目录结构、快速用法、内置工具表与火车查询说明。
- 验证：ruff 零告警；真实查询 2026-11-27「北京南 → 上海虹桥」返回 55 个车次，
  G547 经停站时刻正常。

### 调整：路径规划工具改用高德地图接口（16:17）

- `route_planner_tool.py`：数据源由 Open-Meteo + OSRM 换成高德 `v3/geocode/geo` 与 `v3/direction/driving`；
  删除英文转向类型翻译表，直接使用高德返回的中文 `instruction`。
- `app/config.py` 新增 `amap_key`（读取 `.env` 的 `AMAP_KEY`）。未配置时返回提示文本且不发请求；
  接口 `status != "1"` 时抛 `ToolError`，地理编码与路径规划分别带中文前缀。
- 构造函数新增 `key` 参数（缺省读配置），保留 `http` 注入，便于离线测试。
- `tests/test_ai_tool.py`：路线相关 fixture 与用例改为高德响应结构，新增缺 key、地理编码错误、路径规划错误 3 个用例；
  共 56 个测试全部通过。
- `README.md` 更新数据源与「配置」一节（`.env` 中的 `AMAP_KEY`）。
- 验证：本次改动文件 ruff 零告警；未配置 key 时提示正确。真实调用需先在 `.env` 填入高德 Web 服务 Key。

### 功能：新增路径规划工具 `RoutePlannerTool`（16:15）

- 新增 `app/ai_tool/route_planner_tool.py`：`plan_route(origin, destination)` 先用 Open-Meteo 地理编码解析地名，
  再调用 OSRM 公共驾车路线接口，两者均无需密钥。
- 返回 JSON：起终点、`distance_km`、`duration_min` 与最多 12 段中文路段指引，超出部分记入 `steps_truncated`。
- 地名找不到、无可行路线、参数不全时返回中文说明；网络异常由 `ToolRegistry` 兜底。
- `__init__.py` 导出 `RoutePlannerTool`；`app/page/ai_chat_test.py` 注册该工具并补充系统提示。
- `tests/test_ai_tool.py` 新增 7 个用例（成功规划、起点/终点找不到、无路线、缺参数、路段截断、异常透传），
  并把真实工具注册断言扩展为三个工具；共 53 个测试全部通过。
- `README.md` 更新目录结构、快速用法与内置工具表。
- 验证：ruff 零告警；真实查询「杭州 → 上海」返回 171.0 km / 125 分钟，指引文案可读。

### 修复：`app/page/ai_chat_test.py` 导入被误改（16:12）

- `from apregistry.py.config import settings` → `from app.config import settings`，并移回 first-party 导入分组。
- 该行疑似全局替换误伤（`app.config` 被拼进了 `registry.py`）；全项目已确认无同类残留。
- 验证：模块可正常导入，`SYSTEM_PROMPT` 输出正确；ruff 零告警。

### 调整：`BaseTool` 契约字段改为小写（16:11）

- `NAME` / `DESCRIPTION` / `PARAMETERS` → `name` / `description` / `parameters`，按"可被子类覆盖的接口字段"语义统一。
- 涉及：`tool_registry.py`（基类、`definition()`、`register()`）、两个工具类、`tests/test_ai_tool.py`、`README.md`。
- 验证：46 个单元测试通过；ruff 零告警；真实天气与搜索调用正常。

### 文档：`app/ai_tool/README.md`（16:06）

- 说明模块结构、快速用法、核心类职责、内置工具参数与数据源。
- 给出新增工具的完整示例与编写约定（唯一名字、参数校验、`ToolError`、`NetClient` 注入）。
- 附 `ToolRegistry.execute()` 的错误处理对照表与测试运行方式。
- 验证：ruff 零告警；22 个工具单元测试通过。

### 调整：`registry.py` → `tool_registry.py`（16:05）

- 文件名与核心类 `ToolRegistry` 对齐；合并后的 `BaseTool`、`ToolError`、`NetClient` 仍在同一模块。
- 包内 3 处导入同步更新：`__init__.py`、`meteo_weather_tool.py`、`web_search_tool.py`。
- 验证：22 个工具单元测试通过；ruff 零告警。

### 调整：`base_tool.py` 与 `net_client.py` 合并进 `registry.py`（16:05）

- `registry.py` 现同时包含 `ToolError`、`BaseTool`、`NetClient`、`ToolRegistry`，按依赖顺序排列。
- 删除 `base_tool.py`、`net_client.py`；包内导入统一为 `from app.ai_tool.registry import BaseTool, NetClient`。
- `__init__.py` 对外导出不变（`BaseTool`、`ToolError`、`ToolRegistry`、两个工具）。
- 目录从 6 个文件减为 4 个：`__init__.py`、`registry.py`、`meteo_weather_tool.py`、`web_search_tool.py`。
- 验证：46 个单元测试全部通过；ruff 零告警；真实天气/搜索调用正常。

### 增强：工具支持注入 `NetClient`，新增离线单元测试（16:02）

- `MeteoWeatherTool` / `WebSearchTool` 的 `__init__` 新增可选参数 `http: NetClient | None = None`，
  默认自建客户端；测试可注入假实现，不再依赖真实网络。
- 新增 `tests/test_ai_tool.py`（22 个用例，全部离线）：
    - `ToolRegistry`：函数定义格式、按名分发、空参数、非法 JSON、非对象、未知工具、`ToolError` 透传、
      意外异常兜底、重名拒绝、真实工具注册。
    - 天气工具：当天含实况、指定日期不带实况、日期越界提示、城市不存在、空城市不发起请求、网络异常转为 `ToolError`。
    - 搜索工具：结果解析（标题 / 链接 / 摘要）、条数上限与钳制、无结果提示、空搜索词不发起请求。
- 验证：`python -m unittest discover -s tests` 共 46 个用例全部通过；ruff 零告警。

### 调整：`base.py` → `base_tool.py`（15:50）

- 文件名与类名对齐（`BaseTool` / `ToolError` 所在模块）。
- 包内 5 处导入同步更新：`__init__.py`、`registry.py`、`net_client.py`、两个工具文件。
- 验证：ruff 零告警；注册表用例与真实工具调用全部通过。

### 调整：`net.py` → `net_client.py`，类 `HttpClient` → `NetClient`（15:48）

- 文件名与类名同步：`app/ai_tool/net_client.py` 中定义 `NetClient`。
- `meteo_weather_tool.py` / `web_search_tool.py` 导入与实例化同步更新。
- 验证：ruff 零告警；注册表用例与真实天气、搜索调用全部通过。

### 调整：`http_client.py` 更名为 `net.py`（15:47）

- 避免模块名看起来像第三方 HTTP 客户端包；实际无冲突（项目内均为 `app.ai_tool.*` 绝对导入，venv 中无同名包）。
- `meteo_weather_tool.py` / `web_search_tool.py` 导入改为 `from app.ai_tool.net import HttpClient`。
- 验证：ruff 零告警；注册表用例与真实天气、搜索调用全部通过。

### 调整：`http_client.py` 改用 `HttpClient` 类封装（15:45）

- 模块级函数 `fetch_json` / `fetch_text` / `_open` 收进 `HttpClient` 类，改为实例方法。
- 超时由构造参数 `HttpClient(timeout=...)` 决定，不再每个调用点传：天气 10 秒、搜索 15 秒。
- `meteo_weather_tool.py` / `web_search_tool.py`：各自在 `__init__` 里持有 `self.http = HttpClient(...)`，
  调用改为 `self.http.fetch_json()` / `self.http.fetch_text()`。
- 验证：注册表用例与真实天气、联网搜索全部通过；ruff 零告警。

### 重构：`app/ai_tool` 封装为通用工具模块（15:44）

- 新增 `base.py`：`BaseTool` 抽象基类统一定义 `NAME` / `DESCRIPTION` / `PARAMETERS`，`definition()` 生成 OpenAI
  函数定义；`ToolError` 表示可预期的执行失败。
- 新增 `registry.py`：`ToolRegistry` 负责 `register()`、`definitions()`、`execute(name, arguments)`；
  JSON 解析失败、未知工具、网络异常、意外异常全部转成中文文本返回给模型，对话循环不再中断。
- 新增 `http_client.py`：`fetch_json` / `fetch_text` 统一 User-Agent、超时，并把 `URLError` / `HTTPError` /
  `TimeoutError` 统一收成 `ToolError`。
- 新增 `__init__.py`：对外只暴露 `BaseTool`、`ToolError`、`ToolRegistry`、`MeteoWeatherTool`、`WebSearchTool`。
- `meteo_weather_tool.py` / `web_search_tool.py`：删掉各自的 `tools()` / `execute()` 与重复的异常处理，
  改为继承 `BaseTool` 只实现 `run()`，实际查询保留为 `get_weather()` / `search()`。
- `app/page/ai_chat_test.py`：改用 `ToolRegistry`，删除 `_execute_tool()` 与逐工具循环。
- 验证：注册表 9 项用例（分发 / 空参数 / 非法 JSON / 非对象 / 未知工具 / ToolError / 意外异常 / 多余参数 / 重名）
  全部符合预期；真实天气与联网搜索均返回数据；ruff 检查新增文件无告警。

### 修复：`app/api/book.py` 监听地址写错导致启动失败（15:38）

- `uvicorn.run(app, host="127.0.0.0", ...)` → `host="127.0.0.1"`。
- 原因：`127.0.0.0` 不是合法的单机回环地址（回环网段是 `127.0.0.0/8`，可分配给网卡的具体地址从 `127.0.0.1` 起），
  系统 binder 拒绝绑定，抛 `[Errno 49] can't assign requested address`。

### 精简：`SerializableMixin` 从 180 行压回 86 行（09:51）

- 移除循环引用检测、`__slots__`/父类私有字段支持、`ClassVar` 过滤、注解缓存、日期/`Enum`/`Decimal` 转换。
- 保留核心：私有字段往返回填、`Optional`/`list`/`dict`/`tuple` 还原、`strict` 未知字段校验。
- 验证：隔离脚本与真实图书数据往返均通过（借阅列表 `stock=[3, 2]` 不变），PyCharm 零警告。
- `docs/SerializableMixin代码分析.md` 同步改写为精简版。

### 优化：`SerializableMixin` 双向对称，仅依赖标准库（09:49）

- 修复私有字段往返丢失：`from_dict` 构造后扫描实例字段，建「剥名 → 实际名」映射并直接写底层属性，`BookNew.stock`
  借阅状态重载后不再回退（实测 4 保持 4）。
- 扩展 `_decode`：支持 `Optional/Union`、`list/set/frozenset/tuple/dict`、`Enum`、日期、`Decimal`；`_dump` 同步转换，
  并增加循环引用检测。
- `from_dict` 新增 `strict` 参数：未知字段默认丢弃、严格模式抛 `ValueError`。
- 次要修复：`_strip` 遍历 MRO 支持父类私有字段；过滤 `ClassVar`；`@cache` 缓存注解；`__dict__` 与 `__slots__` 合并读取；
  `exclude` 类型放宽为 `Collection[str]`。
- 验证：隔离脚本 9 项全部通过；真实图书/会员数据往返一致（借阅列表 `stock=[3, 2]` 保持不变）；两个文件 PyCharm 零警告。
- 同步更新 `docs/SerializableMixin代码分析.md` 为优化后版本，移除第三方库方案建议。

### 文档：新增《SerializableMixin 代码分析》（09:41）

- 分析 `app/mixins/serializable_mixin.py`：`to_dict` 与 `from_dict` 不对称，导入侧存在静默丢字段。
- 实测确认三个缺陷：私有字段 `stock` 往返丢失（4 → 5）、`Optional[模型]` 保持 dict、`tuple` 注解回传 list。
- 另列未知字段被吞、`_dump` 与 JSON 边界不齐（`set/datetime/Enum`）、父类私有字段前缀不剥离等次要问题，并给出轻量声明与换
  pydantic/msgspec 两条路线。
- 文档路径：`docs/SerializableMixin代码分析.md`，附录含可复现的隔离验证脚本与输出。

### 文档：新增《PyCharm 侧边栏 Claude Agent 一直显示正在准备》排查报告（09:15）

- 依据 `idea.log` 梳理时间线：09:04 npm 安装超时 → 09:08 重装 → 09:10 进程启动成功 → 09:10:43 转入终端登录等待。
- 结论：安装已完成，卡在 `claude auth login --console` 授权；根因是 PyCharm 以 `--hide-claude-auth` 启动，
  不接受 claude.ai 订阅，只认 API key / Enterprise。
- 文档路径：`docs/PyCharm侧边栏ClaudeAgent一直显示正在准备.md`，含三种处理方案与日志排查顺序。

### 修复：`member.json` 为字典格式时加载报 `'str' object has no attribute 'items'`

- 原因：`resources/member.json` 顶层是 `{卡号: 会员}` 字典，`for e in items` 取到的是 key 字符串，`from_dict("N001")`
  中 `data.items()` 失败。
- 修复：图书与会员加载都兼容两种顶层格式——`rows = items.values() if isinstance(items, dict) else items`。
- 验证：加载 5 本图书 / 7 个会员，`V001` 正确还原为 `VipMemberNew`（`vip_level=1`），`N002` 的借阅记录 `《C++程序设计》`
  一并还原；菜单运行正常，PyCharm 零警告。

### 类型标注：`create_books_json` / `create_members_json` 的 `f` 改为 `TextIO`

- `f: Any` → `f: TextIO`（`from typing import TextIO`），两个同类方法统一，并加 `@staticmethod`。
- 修复：`__init__` 中 `open(..., "wr")` 为非法模式（运行时 `ValueError`），改为 `"r+"`，PyCharm 由此正确推断
  `TextIOWrapper`，「应为 TextIO，但实际为 IO[Any]」警告消失。
- 验证：`LibraryNew()` 正常加载 5 本图书 / 7 个会员，PyCharm 零警告。

## 2026-11-23

### 修复：`book_look` 书名误输出为 `total_num`

- `LibraryNew.book_look` 中 `书名: {book.total_num}` 改为 `book.title`。
- 验证：查看借阅时书名显示正确。

### 重构：`LibraryNew` 资源路径抽为类变量

- 新增类变量 `BOOKS_JSON` / `MEMBERS_JSON`，替换 `__init__` 与 `load_json` 中重复的 `"resources/*.json"` 字面量。
- 验证：`cache_json()` 写出/读回正常，系统加载图书与会员正常，PyCharm 零警告。

### 注释：`SerializableMixin.from_dict` 逐行补充中文说明

- 为 `from_dict` 的每一行加中文注释（形参过滤、构造实例、读取注解、还原非构造字段、返回），行为不变。
- 验证：`BookNew` / `NormalMemberNew` 往返序列化正常，PyCharm 零警告。

### 重构：`SerializableMixin` 统一序列化，移除模型内手写的 `from_dict` / `to_dict`

- 封装：`SerializableMixin` 接管模型 ↔ 字典互转——`to_dict` 遍历实例属性、去掉私有字段的名字修饰（`_BookNew__stock` →
  `stock`）、嵌套模型与列表递归展开；`from_dict` 按 `__init__` 形参构造，类注解声明的非构造字段（如 `books`）按类型还原后回填。
- 简化：`BookNew` / `MemberNew` 改为继承 mixin，删除各自手写的方法；`VipMemberNew` 的 `to_dict` 覆盖也删除
  （`vip_level` 在实例属性中，自动输出）。
- 标注：`MemberNew` 增加类注解 `books: list[BookNew]`，供 `from_dict` 递归还原图书列表。
- 验证：图书 / 会员 / VIP 往返序列化正确，嵌套 `books` 还原为 `BookNew`；运行借阅 → 查看 → 退出正常，PyCharm 零警告。

### 修复：`MemberNew.from_dict` 意外实参，补全 `LibraryNew` 会员加载

- 原因：`books` 不是 `__init__` 形参，`cls(..., books=...)` 被 PyCharm 报「意外实参」，运行时会 `TypeError`。
- 修复：`from_dict` 按 `__init__` 形参过滤后 `cast(type[Any], cls)(**kwargs)` 构造，再回填 `BookNew` 列表；
  签名补为 `data: dict[str, Any] -> Self`，`VipMemberNew` 的 `vip_level` 由形参过滤自动匹配。
- 修复：`LibraryNew.__init__` 中未写完的 `if "level" in e: ... else:`（语法错误）补全为按 `vip_level` 分派
  `VipMemberNew` / `NormalMemberNew`；`load_json` 加 `@staticmethod` 消除弱警告。
- 验证：PyCharm 检查零报错；运行借阅（9787115546081）→ 查看 → 退出正常。

### 修复：`SerializableMixin.from_dict` 的「意外实参」警告

- 原因：`cls` 被推断为 `type[Self]`，而 mixin 自身没有 `__init__`，PyCharm 按 `object.__init__` 校验
  `cls(**kwargs)`，误报「意外实参」。
- 修复：改为 `cast(type[Any], cls)(**kwargs)` 调用；补全类型注解（`data: dict[str, Any]`、返回 `Self`、
  `to_dict(exclude: tuple[str, ...] = ()) -> dict[str, Any]`），`from_dict` 顺带保留「多余字段丢弃」的说明。
- 验证：PyCharm 检查零警告；`Book.from_dict` 正确丢弃 `stock`/`extra` 并使用默认值，`to_dict(exclude=...)` 排除生效。

### 调整：`book_system_new.py` 图书改用真实 ISBN，新增 `resources/book.json` 导出

- 数据：5 本书改为硬编码真实书目（Python编程、C++程序设计、Java编程思想、C程序设计、JavaScript高级程序设计），
  `book_id` 直接使用 isbn。
- 新增 `read_json()`：把 5 本图书以列表写入 `resources/book.json`，供后续读取练习；`__main__` 改为调用它。
- 修复：`write_json` 增加 `default=lambda o: o.to_dict()`，解决
  `TypeError: Object of type BookNew is not JSON serializable`；
  新增 `BookNew.to_dict()`，库存输出为 `stock` 而不是私有字段 `_BookNew__stock`。
- 新增 `MemberNew.to_dict()`：输出 `member_id` / `name` / `password` / `books`（借阅中的图书展开为列表）；
  `VipMemberNew` 重写并在基础字段上追加 `vip_level`。
- 验证：在 `app/page/classroom` 下运行，生成 5 条合法 JSON（book_id / title / author / total_num / stock）。

### 新增文档：`docs/python可变参数默认值注意点.md`

- 内容：解释 `ModelTest` 中 `data: dict = {}` / `items: list = []` 导致 a、b 实例共享同一对象的原因
  （默认值在 `def` 时创建一次，存于 `__init__.__defaults__`）、共享可变状态的危害，以及 `None` 哨兵修复写法与判断规则。
- 补充：新增「`data or {}` 与 `is not None` 的区别」一节，含假值（`{}`/`[]`/`0`/`""`）对比实测、语义对照表与 `or` 适用场景。
- 补充：新增「适用范围：所有函数，不只 `__init__`」一节，覆盖 `__defaults__` / `__kwdefaults__`、实例/静态/类方法、`lambda`、
  重新 `def` 即新建，以及与类属性、`@dataclass`、pydantic 默认值的对比。

### 修复：`ReprMixin.__repr__` 遇到自定义对象抛 `TypeError`

- 原因：`json.dumps(self.__dict__)` 只认 JSON 原生类型，`MemberNew.books` 里是 `BookNew` 实例，序列化时抛
  `TypeError: Object of type BookNew is not JSON serializable`。
- 修复：`repr_mixin.py` 增加 `_json_default` 兜底函数，自定义对象转 `__dict__`（嵌套输出为字典）、集合/元组转列表、其余转
  `str`，并作为
  `json.dumps(..., default=...)` 传入。
- 验证：模拟登录 → 借书 → 查看借阅 → 退出，会员与图书均正常打印；`Book`（pydantic）自身 `__repr__` 不受影响。

### 新增：`book_system_new.py` 借还书交互功能

- 原因：`run()` 缩进在 `__init__` 内部，只是局部函数而非方法；PyCharm 只对类体中直接定义的方法做 `self` 类型推断，局部函数里的
  `self` 是无标注参数，故 `self.login()` 等未定义调用不报警。
- 修复：`run` / `login` / `book_borrow` / `book_back` / `book_look` 全部移回类体并实现；`run` 改为登录失败即退出，菜单增加无效选项提示。
- 借还逻辑：按 `book_id` 查字典取书，校验库存与「是否本人借阅」；借出扣库存并加入会员 `books`，归还加库存并移出列表。
- 清理：恢复乱码书名（如 `《Python编程》`）与会员姓名为正常中文；`VipMemberNew` 去掉多余的 `ReprMixin` 基类。
- 验证：`PYTHONPATH=app .venv/bin/python ...` 模拟登录 → 借书 → 查看 → 还书 → 查看 → 退出，输出正确。

### 修复：`book_system_new.py` 语法与运行时错误

- 语法：`book id=` → `book_id=`、`total num=` → `total_num=`；字典值里的 `password:` / `vip _level:` / `vip level:` 冒号改为等号；
  `"E\"` 这类被转义引号截断的字符串恢复为完整字符串。
- 运行时：`NormalMemberNew` 原为 `pass` 空类，无法接收构造参数，改为继承 `MemberNew`；`VipMemberNew` 调用 `super().__init__`
  时缺少 `books` 参数且形参与实参名 `pwd`/`password` 不一致，统一为 `password` 并补传 `books`。
- 健壮性：`books` 改为 `list[BookNew] | None = None` + `books or []`，避免可变默认参数被所有实例共享；`member_id` 类型注解由
  `int` 改为 `str`（实际使用 N001 这类卡号）。
- 清理：删除 ORM/OCR 残留的乱码书名与会员名，书名与作者保持一致、会员名统一为 `会员{卡号}` 占位；补充 `__main__` 打印示例。
- 验证：`PYTHONPATH=app python app/page/classroom/book_sys/bookNew.py` 正常输出图书与 VIP 会员信息，无报错。

## 2026-11-22

### 修复：`plot_demo.ipynb` 中文字体在 macOS 上缺失

- 原因：`font.sans-serif` 只配置了 `SimHei`（Windows 自带字体），macOS 无此字体，matplotlib 回退失败并刷出
  `findfont: Generic family 'sans-serif' not found` 警告，中文显示为方块。
- 修复：改为跨平台字体列表 `['Heiti SC', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']`，并补充
  `axes.unicode_minus = False` 防止负号显示异常。
- 修复：`plt.figure(figsize=(10, 6))` 移到 `plt.plot()` 之前，避免折线画在默认图上、`show()` 显示的却是新建空白图。
- 验证：`python3` 以 Agg 后端渲染中英文坐标轴，零警告。

## 2026-11-21 21:14

### 调整：`movie_system_oo.py` 更名为 `movie_system_new.py`

- 调整：`app/page/curd/movie_system_oo.py` → `movie_system_new.py`，测试文件同步更名为 `tests/test_movie_system_new.py`
  ，导入路径与运行命令一并更新。
- 验证：`python -m unittest tests.test_movie_system_new` 与 `discover -s tests` 均 24 项通过；PyCharm 零警告。

## 2026-11-21 21:07

### 简化：移除 `movie_system_oo.py` 中的套壳方法

- 调整：删除 `add_movie` / `update_movie` / `delete_movie` / `query_movie` / `list_movies` 五个仅转发 `self.crud` 的方法，
  `run()` 直接调用 `crud.add()` / `update()` / `delete()` / `query()` / `show()`。
- 影响：`MovieSystem` 不再暴露需求文档中的同名方法，CRUD 能力通过 `crud` 与菜单提供；`top_rated_movie` 与 `movie_list` 保留。
- 验证：`python -m unittest tests.test_movie_system_oo` 24 项全部通过；PyCharm 零警告。

## 2026-11-21 21:06

### 调整：`movie_system_oo.py` 改用 ConsoleCrud 实现

- 实现：`app/page/curd/movie_system_oo.py`（原 `movie_system.py` 保持不变）中 `Movie` 保留 `__str__` 与 `update_info`；
  `MovieSystem` 组合 `ConsoleCrud`，导演/主演/票价/评分字段与校验交给组件，`add_movie` / `update_movie` / `delete_movie` /
  `query_movie` / `list_movies` 委托组件，`movie_list` 由字典数据转换为 `Movie`，`top_rated_movie` 单独实现并列输出，菜单扩展为
  1-7 项。
- 测试：`tests/test_movie_system_oo.py` 调整为 24 个用例，覆盖空导演/非数字/票价与评分越界的重新录入、重名、增删改查、空列表、汇总行、并列最高分与菜单流程。
- 验证：`python -m unittest tests.test_movie_system_oo -v` 24 项全部通过；两个文件在 PyCharm 中零警告。

## 2026-11-21 20:59

### 调整：`ConsoleCrud.name_prompt` 属性更名为 `key_prompt`

- 调整：`self.name_prompt` → `self.key_prompt`，与构造参数 `key_prompt` 保持一致；`add` / `update` / `delete` / `query`
  四处读取同步更新。
- 影响：外部若直接访问 `crud.name_prompt` 需改为 `crud.key_prompt`；四个 CRUD 示例均通过构造参数传值，不受影响。
- 验证：以 `key_prompt="书名: "` 实例化后添加与精确查询正常；PyCharm 检查零警告。

## 2026-11-21 20:58

### 新增：`ConsoleCrud` 精确查询方法并接入菜单

- 新增：`query()` 按名称精确查找并展示单条记录，复用 `name_prompt` 与 `format_row`；记录不存在时提示「{entity}不存在」。
- 调整：菜单改为「1.添加 2.修改 3.删除 4.精确查询 5.查询全部 6.退出」，输入提示改为 1-6，`run()` 的 `match`
  分支同步调整；菜单行宽按中日韩字符显示宽度对齐边框。
- 验证：模拟完整流程覆盖添加、精确查询命中/未命中、查询全部、非法编号与退出；PyCharm 检查零警告。

## 2026-11-21 20:45

### 文档：`ConsoleCrud` 五个类型别名补充注释

- 内容：`CrudRow`、`CrudFormatter`、`CrudSummary`、`CrudVerify[T]`、`CrudReader[T]` 上方各加一行注释，说明数据形状、参数与返回值；
  `CrudReader` 注明参数顺序为「提示语 + 校验回调 + 失败提示语」。
- 验证：PyCharm 检查零警告，模块导入正常。

## 2026-11-21 20:45

### 调整：`ConsoleCrud` 类型别名统一加 `Crud` 前缀

- 调整：`Row` → `CrudRow`、`Formatter` → `CrudFormatter`、`Summary` → `CrudSummary`、`Verify[T]` → `CrudVerify[T]`、
  `Reader[T]` → `CrudReader[T]`。
- 配套：`Field` 已更名为 `CrudField`，修正 `__init__` 中遗留的 `Field[Any]`；`app/util/__init__.py` 与三个已跟踪的 CRUD
  示例同步更新导入与类型注解。
- 验证：`console_crud.py` 在 PyCharm 中零警告；mock 输入、`app.util` 导出、五个相关文件编译均通过。

## 2026-11-21 20:38

### 修复：消除 PyCharm 对 `read_` 方法返回值可能为 `None` 的警告

- 原因：PyCharm 的控制流分析对 `while True` + `continue` 组合会认为函数可能隐式返回 `None`，把 `read_float` / `read_int` /
  `read_bool` 的返回类型推断为 `float | None` 等并告警。
- 调整：抽出泛型 `_read[T]` 统一「解析 → 校验 → 重试」循环（`try/else`，不使用 `continue`）；格式校验拆为 `_parse_float` /
  `_parse_int` / `_parse_bool`，用带提示语的 `ValueError` 表达失败原因；四个 `read_` 方法委托给 `_read`。
- 效果：`console_crud.py` 在 PyCharm 中零警告；提示语与重试行为保持不变。
- 验证：mock 输入覆盖格式错误、负数、校验失败、自定义提示、无回调及字段联动；五个 CRUD 相关文件均通过编译。

## 2026-11-21 20:26

### 新增：`Field` 支持自定义校验提示语

- 新增：`Field.verify_hint`（默认 `DEFAULT_VERIFY_HINT = "校验未通过，请重新输入"`），`verify` 返回 False 时打印该提示，可写成「价格必须大于
  0，请重新输入」这类完整说明。
- 调整：`read_str` / `read_float` / `read_int` / `read_bool` 增加第三个参数 `hint`，`_input_row` 透传 `field.verify_hint`
  ；新增 `Reader[T]` 类型别名统一读取函数签名。
- 兼容：`Field(prompt, reader, verify)` 的位置参数不变，`verify_hint` 作为第四个参数可选。
- 验证：mock 输入覆盖四个方法的自定义/默认提示及字段联动；既有 CRUD 示例均通过编译。

## 2026-11-21 20:25

### 完善：`ConsoleCrud` 四个 `read_` 方法统一支持校验回调

- 调整：`read_str` / `read_float` / `read_int` / `read_bool` 均新增 `verify: Verify[T]` 参数，回调收到解析后的类型化值（
  `read_bool` 收到 `bool`），返回 `False` 时提示「校验未通过，请重新输入」并重读。
- 调整：`Field` 改为泛型 `Field[T]`，新增泛型别名 `Verify[T] = Callable[[T], bool]`，约束 `reader` 与 `verify` 的入参类型一致。
- 修复：`read_float` / `read_int` 输入非数字时直接抛 `ValueError` 崩溃，改为提示后重新输入；数值约束由 `> 0` 放宽为 `>= 0`
  ，与原有「非负」提示一致（0 分、0 库存可录入）。
- 修复：`read_bool` 原先校验通过后无条件返回 `True`，与用户输入无关；改为先解析 yes/no 得到 `bool` 再交给 `verify`。
- 验证：mock 输入覆盖格式错误、校验失败、校验放行、无回调四种路径；四个既有 CRUD 示例均通过编译。

## 2026-11-21 15:16

### 重构：`EduManagement` 改为 pydantic 模型，默认值用 `Field(default_factory=dict)`

- 调整：`app/page/classroom/edu_management.py` 中 `EduManagement` 改为 `BaseModel`，删除手写 `__init__`，字段声明为
  `data: dict[str, Student] = Field(default_factory=dict, description="学生数据，按姓名索引")`；`Student` 仍是普通类，故加
  `ConfigDict(arbitrary_types_allowed=True)`。
- 修复：移除 `from dns import update`（PyCharm 误导入，实际是 `dns.update` 模块，调用会报 `module is not callable`），菜单 1/2
  改为调用 `self.update(name)`；末尾 `EduManagement({})` 改为 `EduManagement()`，pydantic v2 不支持位置参数。
- 验证：运行示例并输入 `6` 正常退出；两个实例的 `data` 互不共享（`a.data is b.data` 为 `False`）；`EduManagement(data={...})`
  关键字传参正常。

## 2026-11-21 15:12

### 调整：`EduManagement` 构造参数 `data` 增加默认值

- 调整：`app/page/classroom/edu_management.py` 中 `__init__` 签名改为 `data: dict[str, Student] | None = None`
  ，为空时内部初始化为空字典，`self.data` 类型仍为 `dict[str, Student]`。
- 效果：`EduManagement()` 可直接实例化，不再强制传参；传入字典时行为与之前一致。

## 2026-11-21 13:18

### 回退：`BaseEnum` 退回普通 `Enum`，移除 `int` 混入

- 原因：`int` 混入虽能让标准库 `json.dumps` 直接序列化枚举，但会让 PyCharm 认为成员值必须是 int，三个枚举共 12
  条警告，需在每个枚举类上加 `# noinspection PyTypeChecker`；而项目主要走 FastAPI/pydantic，普通 `Enum` 已按 `value`（即
  code）自动输出数字。
- 调整：`class BaseEnum(Enum)`，`__new__` 恢复 `object.__new__(cls)`；三个枚举的 `# noinspection PyTypeChecker` 一并移除。
- 效果：`json.dumps` 需取 `.code` / `.value`；`enum == 1` 为 `False`；pydantic/FastAPI 仍序列化为 `{"status": 1}`
  ；pickle、查找、`call_extra`、重复 code 校验不受影响。
- 文档：`docs/枚举使用指南.md` 移除 int 比较与抑制说明，恢复 JSON 序列化说明及模板。
- 验证：三个示例脚本运行正常，pydantic 输出 `{"status":1}`，PyCharm lint 四个文件零警告。

## 2026-11-21 13:16

### 优化：`BaseEnum` 混入 `int`，支持原生序列化与 int 比较

- 原因：枚举不是 int 子类时，`json.dumps` 不认，入库/日志/第三方 int 接口都要手动取 `.code`。
- 调整：`app/enums/base_enum.py` 改为 `class BaseEnum(int, Enum)`，`__new__` 用 `int.__new__(cls, code)`；`value` 仍为
  `code`，`code` / `label` / `extra` 行为不变。
- 效果：`json.dumps({"status": UserStatus.ACTIVE})` → `{"status": 1}`；`UserStatus.ACTIVE == 1` 为 `True`；pydantic/FastAPI
  直接按 int 收发；`str()` 仍显示成员名（`UserStatus.ACTIVE`），`repr()` 不变。
- 抑制：`int` mixin 让 PyCharm 认为成员值必须是 int，三个枚举类定义前加 `# noinspection PyTypeChecker`，恢复零警告。
- 文档：`docs/枚举使用指南.md` 更新 API 表、JSON/比较/抑制说明及新增枚举模板。
- 验证：三个示例脚本运行正常；json、pickle、pydantic、`== int`、重复 code 校验均通过；PyCharm lint 四个文件零警告。

## 2026-11-21 11:50

### 文档：新增 `docs/枚举使用指南.md`

- 内容：整理 `BaseEnum` 的定义语法、API 一览表、三个枚举（函数型/字典型/无 extra）的完整示例、注意事项（code 唯一、Enum
  别名、继承限制、JSON 序列化、pickle）以及新增枚举模板。
- 验证：文档中的示例与三个枚举脚本的实际输出一致。

## 2026-11-21 11:48

### 示例：三个枚举补充 `BaseEnum` 使用示例

- 内容：`user_status.py`（函数型 extra）、`review_status.py`（dict 型 extra）、`order_status.py`（无 extra）各自补充 5~7
  段可运行示例，覆盖遍历、`code_of`/`name_of`/`cls(value)`/`cls[name]` 查找、`match_of` 条件查找、`call_extra`、`choices()`
  、序列化取 code 和业务判断。
- 修复：`match_of` 的 lambda 参数由 `e` 改为 `item`，消除“隐藏外部作用域名称”弱警告。
- 验证：三个脚本均正常运行，PyCharm lint 零警告。

## 2026-11-21 11:38

### 重构：`BaseEnum` 改用 `__new__`，让枚举 value 回归 code

- 原因：原实现把 `(code, label, extra)` 整体当 value，`UserStatus(1)` 无法按 code 查找，`code_of` 只能 O (n) 遍历；含 lambda
  时 `pickle` 也会失败。
- 调整：`app/enums/base_enum.py` 用 `__new__` 将 `_value_` 设为 `code`，其余信息挂实例属性；`code_of` 改为 `cls(code)` 查找；
  `name_of` 改用 `__members__`；新增 `__init_subclass__` 校验 code 唯一（基于 `__members__`，能查到别名）、`choices()` 下拉框数据、
  `call_extra()` 统一处理函数型/数据型 `extra`。
- 配套：`user_status.py`、`review_status.py` 调用处由 `getattr(e, "extra")` 改为 `e.call_extra(...)`；`extra` 保持 `Any`，因为
  `ReviewStatus` 存的是 dict。
- 验证：三个枚举脚本运行正常，`UserStatus(2)` / `code_of` / `choices` / 重复 code 报错 / `pickle` 往返均通过；PyCharm lint
  四个文件零警告。

## 2026-11-20 20:03

### 修复：`jn/book_test.ipynb` 读 CSV 报 FileNotFoundError

- 现象：`pandas.read_csv('app/assets/csv/books.csv')` 报 `[Errno 2] No such file or directory`。目录已由 `cvs` 改名为
  `csv`，但 notebook 的 cwd 是 `app/page/jn`，相对路径被解析成 `app/page/jn/app/assets/...`。
- 修复：用 `pathlib` 从 cwd 向上查找 `pyproject.toml` 定位项目根目录，再拼 `app/assets/csv/books.csv`；同时清空上次失败的输出。
- 验证：在 `app/page/jn` 下执行，读到 101 行 9 列，`price > 50` 过滤结果正常。

## 2026-11-20 15:47

### 修复：`jn/test.ipynb` 用 `list.index` 取序号触发 ValueError

- 现象：`properts.index(e)` 内部用 `==` 逐项比较，遇到 `df.size = 3` 时 `RangeIndex == 3` 返回布尔数组，`if` 无法判断真值，抛出
  `ValueError: The truth value of an array with more than one element is ambiguous`。
- 修复：改用 `enumerate(properts)` 直接拿序号，避免元素比较。
- 验证：改写后脚本输出 9 项属性的序号与类型，无异常。

## 2026-11-20 14:51

### 修复：`test.py` 调用处误用注解语法 + `rectangle_area` 注解规范化

- 现象：`print(rectangle_area(l:10, w: 50))` 中 `:` 是定义期注解语法，调用时非法，整个文件 `SyntaxError` 无法运行。
- 修复：改为关键字参数调用 `rectangle_area(l=10, w=50)`；函数签名规范为 `l: float, w: float -> float`，docstring 参数名
  `Z`/`W` 更正为 `l`/`w`。
- 验证：`python app/page/test.py` 正常运行，输出 `500`，`help()` 显示注解与文档一致。

## 2026-11-20 14:45

### 依赖：pandas 锁定 2.x 以匹配 streamlit

- 现象：原环境为 pandas 3.1.0（传递依赖，未在 `pyproject.toml` 声明）。pandas 3 默认字符串 dtype、移除 `applymap`、CoW
  默认开启，streamlit 及生态尚未完全适配。
- 调整：`pyproject.toml` 新增 `pandas>=2.2,<3`，`uv add` 解析并安装 pandas 2.3.3（新增 `tzdata`）；顺带补录已在环境中使用但未声明的
  `ipykernel>=7.4.0`。
- 验证：`AppTest` 跑 `app/page/streamlit_demo.py` 无异常；`st.dataframe` / `st.line_chart` / `st.write` 正常；仅
  `st.table(df.describe())` 在混合 dtype 列上触发 streamlit 的 Arrow 自动修复告警（与 pandas 版本无关）。

## 2026-11-20 10:37

### 修复：`Book.price` 传整数字面量导致类型检查报错

- 现象：`price=66` 被推断为 `Literal[66]`，无法赋值给 `Decimal`；运行期 Pydantic 会自动转换，仅静态检查报错。
- 修复：`app/api/book.py` 引入 `Decimal`，三处 `price` 改为 `Decimal("66")` / `Decimal("77")` / `Decimal("88")`。
- 验证：JSON 序列化仍为 `"66.00"` 等两位小数字符串；`ruff` 通过。

## 2026-11-20 10:33

### 修复：统一开发启动入口与后端调试文档

- `app/main.py` 端口 8000 → 8001，与 README 的启动命令一致。
- `docs/后端调试指南.md` 按本仓库修正：`app.main:app` → `app.api.book:app`；
  Working directory 改为项目根目录；解释器改为 `.venv`（Python 3.13）；
  断点示例改为 `app/api/book.py` 的 `get_books()`；pdb / debugpy 命令同步更新；
  日志一节改为 uvicorn 终端访问日志（原 `/tmp/book_backend_8010.log` 不属于本项目）。
- 验证：文档中已无 `backend` / `book_management_system` / `app.main:app` 残留；
  `import app.api.book` 正常；`ruff` 通过。

## 2026-11-20 09:11

### 调整：`printdlog.py` 改为从零独立实现

- `app/util/printdlog.py` 不再从 `dlog.py` 再导出，改为自包含实现：
  `printdlog(*args, sep=" ", end="\n")` 输出 `[日期时间 文件名.函数名 Line:行]: 内容`，
  调用位置由 `sys._getframe` 跳过本模块封装取得；模块级 `enable_log` / `enable_color` 可配置。
- `app/util/dlog.py` 移除上一版临时加入的 `printdlog` 函数，`DLog` 保持原样。
- `app/util/__init__.py` 不导出 `printdlog`，避免包属性与同名子模块互相覆盖；
  使用 `from app.util.printdlog import printdlog` 导入。
- 验证：模块顶层、嵌套函数、类方法、classmethod 四种调用点定位正确；`sep` / `end` 生效；
  `enable_log = False` 时不再输出；`ruff`、`compileall` 通过。

## 2026-11-20 09:08

### 新增：`printdlog`（`DLog` 的 print 式函数入口）

- `app/util/dlog.py` 新增 `printdlog(*args, sep=" ", end="\n")`：像 `print` 一样调用，
  按 DEBUG 输出，格式与 `DLog(...)` 完全一致（`[时间 DEBUG 文件名.函数名 Line:行]: 内容`）。
- 新增 `app/util/printdlog.py` 做再导出，可 `from app.util.printdlog import printdlog`；
  `app/util/__init__.py` 同步导出。
- 实现直接复用 `DLog._print_log`，不引入第二套日志设施；此前删掉的 logging 版 `printlog` 不再恢复。
- 验证：函数内、类方法、模块顶层三种调用点均正确定位到外部调用处；
  `sep="-", end="!\n"` 生效；`ruff` 通过。

## 2026-11-18 22:07

### 调整：`DLog` 调用位置加上文件名前缀

- `_caller_name` 统一返回「文件名.函数名」：`codable.show_validate`、`Demo.run`、`outer.inner`；
  模块顶层仍只输出文件名（`<string>` / `dlog.py`）。
- 模块 docstring 同步更新格式说明。
- 验证：`codable.py` 输出 `[时间 DEBUG codable.show_validate Line:36]: ...`；
  类方法、`classmethod`、嵌套函数、模块顶层四种形态均正确；`ruff` 通过。

## 2026-11-18 22:04

### 调整：`codable.py` 日志改用项目自带的 `DLog`

- 曾用标准库 logging 实现了一版 `printlog`（`stacklevel=2` 让 logging 定位调用点），随后删除，
  避免项目里出现两套日志工具。
- `app/page/codable.py` 改用 `DLog`：普通输出用 `DLog(...)`（构造时打印，支持多个参数），
  非法输入用 `DLog.e(...)` 走 ERROR 级别；同时删除本地 `sys._getframe` 版本与临时的环境变量调试打印。
- 验证：输出 `[时间 DEBUG 函数名 Line:行号]: 内容`，ERROR 两条正确；全仓库已无 `printlog` 残留；`ruff` 通过。

## 2026-11-18 21:47

### 优化：关闭 Pydantic 插件加载，脚本启动从 0.67s 降到 0.32s

- 现象：`app/page/codable.py` 这类只定义几个模型的小脚本也要等几百毫秒。
  用 `-X importtime` 定位到：定义 `Book` 类耗时 446ms，其中 logfire + opentelemetry + requests 约 350ms。
- 原因：Pydantic V2 首次定义模型时扫描 `pydantic` 插件入口，`pydantic-ai` 附带的 `logfire-sdk`
  注册了一个插件，被无条件导入。
- 修复：`sitecustomize.py` 中 `os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")`。
- 新增 `docs/Pydantic启动变慢.md`：记录现象、实测数据、源码位置、三个方案与 `-X importtime` 排查方法。
- 验证：脚本耗时 0.67s → 0.32s；`get_plugins()` 返回空；`codable.py` 输出完整；`ruff`、`compileall` 通过。

## 2026-11-18 21:21

### 调整：`codable.py` 的打印统一加函数名前缀

- 新增 `log()` 辅助函数，用 `sys._getframe(1).f_code.co_name` 取调用方函数名，输出形如 `[show_validate] ...`。
- 所有 `print` 改为 `log`，包括多行的 `model_dump_json` 输出；`main()` 增加一行总标题。
- 验证：实跑输出每行都带 `[函数名]` 前缀，`ruff check` 通过。

## 2026-11-18 21:18

### 示例：`app/page/codable.py` 演示 `Book` 模型的 JSON 转换

- 按《Pydantic V2 的 `model_validate` / `model_dump` 命名》的四个方法矩阵重写该文件：
  入口 `model_validate` / `model_validate_json`，出口 `model_dump` / `model_dump_json`。
- 覆盖要点：`"1"` → `int`、`"66.60"` → `Decimal` 的类型转换；`model_dump` 保留 `Decimal`、
  `model_dump_json` 输出两位小数字符串；往返后模型相等；`exclude` / `include` 用法；
  非法 `price` / `isbn` 在入口被 `decimal_parsing`、`string_pattern_mismatch` 拦下。
- 验证：脚本实跑输出符合预期，`ruff check` 通过。

## 2026-11-18 20:12

### 文档：清理 `docs/` 中残留的 `lib/`、`../app` 旧路径

- `docs/PyCharm-Streamlit外部工具配置.md`：`lib/page/streamlit_demo.py` → `app/page/streamlit_demo.py`，
  `lib.base_widget` → `app.base_widget`，报错示例 `No module named 'lib'` → `'app'`，
  绝对路径示例 `~/GitHub/...` 改为当前仓库路径。
- `docs/Python-Literal类型.md`：两处 `../app` 还原为 `app/base_widget/_layout.py`、`app/base_widget/flex.py`，
  枚举对比处补上 `app/enums/weekday_enum.py`、`app/enums/member_level_enum.py`。
- `docs/Python-Callable与code属性.md`：两处 `../app` 还原为 `app/util/hook.py`、`app/util/dlog.py`。
- 验证：`docs/` 下已无 `lib/`、`lib.`、`../app`、`GitHub/python_templet` 等旧引用。

## 2026-11-18 20:10

### 文档：同步模型改造后的类名与该有的说明

- `docs/Pydantic后端必备.md`：`StudentModel` → `Student`；补上 `Student` 已全部改用 `Field` 约束
  （`min_length`、`ge/le`、`str_strip_whitespace`）的现状；`total_score` 处一并提到 `average_score`。
- `docs/Python-property装饰器.md`：`StudentModel.total_score` → `Student.total_score`。
- 两篇里被误写成 `../app/model/student.py` 的路径改回 `app/model/student.py`。

## 2026-11-18 20:07

### 重构：`BookLibraryModel` 更名为 `BookLibrary`，文件同步改名

- `app/model/book_library_model.py` → `app/model/book_library.py`（`git mv` 保留历史），类名 `BookLibraryModel` →
  `BookLibrary`。
- 调用方同步：`app/page/data_type_test.py`、`app/page/book_managment_system/book_managment_system.py` 改为
  `from app.model.book_library import BookLibrary`，实例化直接 `BookLibrary()`。
- `docs/Pydantic后端必备.md` 三处路径/类名同步更新；全仓库已无 `book_library_model` 残留。
- 验证：管理页、`data_type_test.py` 实跑正常，`compileall app` 通过；`ruff` 仅剩管理页第 84 行既有的 `print(f"退出系统")`
  告警，非本次引入。

## 2026-11-18 20:04

### 调整：`Student.total_score` 恢复 `sum([...])` 写法

- 按需求把上一轮简化的直接相加改回 `sum([self.chinese, self.math, self.english])`，便于以后增删科目。
- 验证：总分 240、平均分 80.0；`ruff check` 通过。

## 2026-11-18 20:03

### 优化：`Student` 字段改用 `Field`，去掉三个问题方法

- `app/model/student.py`：`student_id` / `name` 加 `min_length=1`；三科成绩加 `ge=0, le=100`；
  全部字段补 `description`；新增 `model_config = ConfigDict(str_strip_whitespace=True)`。
- 删除 `__str__`（字符串未闭合，输出永远截断在 `", "`）、`__eq__` / `__lt__`（全项目无调用，且 `__eq__` 把语义悄悄改成只比学号）、
  `to_dict`（只是 `model_dump(mode="json")` 的包装，且无人调用）。
- `total_score` 顺带去掉多余的列表推导，`average_score` 保持不变。
- 验证：总分 240 / 平均 80.0；`userName` 别名可用；首尾空格被去掉；`repr` 不显示密码；
  空学号 / 空姓名 / 负分 / 超 100 / 缺字段分别被 `string_too_short`、`greater_than_equal`、`less_than_equal`、`missing` 拦截；
  `compileall app`、`ruff check` 通过。

## 2026-11-18 19:59

### 文档：新增《Python 里给方法加 `@property` 是什么意思》

- 新增 `docs/Python-property装饰器.md`：普通方法与属性的对比、`@property` 的四个作用、三个限制
  （只读、Pydantic 中不进 `model_dump`、每次重算），以及选型速查表。
- 全部示例对应本项目代码：`StudentModel.total_score`、`Settings.vision_model`、`@computed_field` 写法。

## 2026-11-18 19:52

### 文档：按 `pyproject.toml` 的依赖版本校准 Pydantic 说明

- `docs/Pydantic后端必备.md` 新增「本项目依赖版本」表：`pydantic==2.14.2`、`pydantic-settings>=2.13.1`、
  `pydantic-ai==2.65.0`、`fastapi>=0.162.0`、Python 3.13，并标注 `==` 锁定的升级注意事项。
- 示例全部换成当前代码：`Book.model_validate`、`Book` 的 `Field` 约束与 `Decimal` 价格、`field_serializer`、
  `app/config.py` 的 `SettingsConfigDict` / `extra="ignore"`；补上「Decimal 在 JSON 中是字符串」这一条。
- 删除已过时的 `Book.from_dict` 建议（该方法已在 19:35 那轮重构中移除）。
- 顺带修复 `pyproject.toml` 第 15 行被误写成 `"-settings>=2.13.1"` 的依赖名，恢复为 `"pydantic-settings>=2.13.1"`；
  `uv lock --check` 通过。

## 2026-11-18 19:50

### 重构：用 `pydantic-settings` 统一读取 `.env` 配置

- 新增 `app/config.py`：`Settings(BaseSettings)` 声明 `ANTHROPIC_*` 四项配置，`env_file` 固定指向项目根 `.env`，
  `extra="ignore"` 兼容其余键；`load_dotenv()` 只在这里调用一次，第三方 SDK 仍能从环境变量读到配置。
  `vision_model` 属性在未配置视觉模型时回退到默认模型。
- `app/page/ai_client.py`、`app/page/ai_robot/llm_client.py`：删掉各自的 `load_dotenv()` 与 `os.getenv`，改读 `settings`。
- `app/page/ai_robot/app.py` 重命名为 `chat.py`：原名与 `app` 包同名，在「脚本目录进 `sys.path`」的场景下会遮蔽
  包导入，导致 `from app.config import settings` 失败（已复现并修复）；README 两处启动命令同步更新。
- `pyproject.toml` / `uv.lock`：`pydantic-settings>=2.13.1` 由间接依赖改为直接依赖。
- 验证：`.env` 键正确读入；`ANTHROPIC_MODEL=env-wins` 时环境变量优先；视觉模型回退生效；
  在脚本目录优先的路径下 `import llm_client` 通过；`chat.py` 以 bare 模式执行无导入错误；`compileall app` 通过。

## 2026-11-18 19:40

### 调整：`Book.price` 由 `float` 改为 `Decimal`

- `price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=8, decimal_places=2)`：
  超过两位小数、负数、非数字输入在校验层直接拒绝（`decimal_max_places` / `greater_than_equal` / `decimal_parsing`）。
- 新增 `@field_serializer("price", when_used="json")`：JSON 输出统一为两位小数字符串（如 `"66.00"`），
  接口返回的 `price` 类型由 number 变为 string，前端需按字符串处理。
- 验证：`66` / `"66.6"` / `66.66` 通过，`66.666` / `1.005` / `-0.01` / `"abc"` 被拒绝；`Decimal("66.60") * 3` 得 `199.80`；
  `/books` 返回 200 且 `price: "66.00"`；管理页、`data_type_test.py`、`compileall app`、`ruff check` 均通过。

## 2026-11-18 19:39

### 优化：`Book` 默认值改用 `Field` 并加校验约束

- `id` / `price` / `stock` 加 `ge=0`，拒绝负值；`title` / `author` 加 `min_length=1`，拒绝空串；
  `isbn` 加 `pattern=r"^\d{13}$"`（现有 100 条数据均为 13 位纯数字，已核对）。
- 字段说明从下方的字符串字面量改为 `Field(description=...)`，FastAPI 的 `/docs` 才能显示。
- 新增 `model_config = ConfigDict(str_strip_whitespace=True)`，输入自动去首尾空格。
- 未改 `price` 的类型（仍为 `float`），换 `Decimal` 涉及接口序列化与页面金额计算，留待单独评估。
- 验证：100 条 `books.json` 正常载入；空书名 / ISBN 位数不符 / 负价格 / 负库存均被拒绝；
  JSON Schema 中各字段 description 正确；两个使用方页面与 `compileall app` 通过。

## 2026-11-18 19:35

### 优化：`Book` 去掉冗余魔术方法，`BookLibraryModel` 复用查找逻辑

- `app/model/book.py`：删除 `from_dict`（只是 `model_validate` 的包装）、`__str__`（输出漏了 `id`，不如 Pydantic 默认 `repr`）、
  `__eq__` / `__lt__`（全项目无依赖，且 `__eq__` 悄悄把相等语义改成了只比 ISBN）。
- `app/model/book_library_model.py`：`Book.from_dict(item)` 改为 `Book.model_validate(item)`；
  `borrow_book` / `return_book` 改用 `find_book_by_isbn`，删掉两处重复的 `enumerate + next` 索引查找。
- 验证：`data_type_test.py`、`book_managment_system.py`（借书 / 还书 / 查借阅 / 退出）实跑正常；
  借还的不存在 ISBN 返回 False，删除后数量正确，默认相等语义恢复为全字段比较；`compileall app` 通过。

## 2026-11-18 19:30

### 文档：新增《后端开发中 Pydantic 要掌握到什么程度》

- 新增 `docs/Pydantic后端必备.md`：按「必须熟练 / 应该知道 / 先跳过」三层划分掌握范围，
  每层都对应到本项目 `app/model/` 下的现有写法，并列出三个高频坑。

## 2026-11-18 19:25

### 修复：`app/main.py` 的 uvicorn 入口指向错误的模块

- 报错 `Attribute "app" not found in module "app.main"`：FastAPI 实例声明在 `app/api/book.py`，`app/main.py` 里没有 `app`
  变量。
- 改为 `uvicorn.run("app.api.book:app", ...)`。
- 验证：`GET /` 返回欢迎信息、`GET /books` 返回图书列表，均 200。

## 2026-11-18 19:12

### 配置：新增 PyCharm 运行配置 `main`

- `.idea/runConfigurations/main.xml`：共享运行配置，脚本 `$PROJECT_DIR$/main.py`，工作目录项目根。
- 解释器显式指向 `$PROJECT_DIR$/.venv/bin/python`（不依赖模块 SDK，因为 `.iml` 里的 SDK 还指向已删除的旧克隆）。
- 验证：XML 可解析、解释器存在、`app/main.py` 实跑输出 `Hello world!`；`.idea/` 在 `.gitignore` 中，该文件仅本地生效。

## 2026-11-18 18:51

### 功能：`ConsoleCrud` 新增布尔值读取方法 `read_bool`

- `read_bool(tips) -> bool`：沿用 `read_float` 的循环重试写法，非法输入打印提示后重新录入。
    - 真值：`y` / `yes` / `true` / `1` / `是`；假值：`n` / `no` / `false` / `0` / `否`。
    - 输入自动去首尾空格并忽略大小写。
- 验证：各真/假写法、大小写、含空格输入，以及「非法输入 → 重新录入」均实测通过；
  `py_compile`、`ruff check` 通过。

## 2026-11-18 15:48

### 调整：`shopping_cart.py` 的 `format_row` / `summarize` 改为独立函数

- 去掉 `ConsoleCRUD(...)` 里的两个 lambda，抽成模块级函数 `format_item` / `summarize_cart`，
  与 `students_crud.py` 的 `format_student` / `summarize_students` 写法一致。
- 验证：查询输出 3 条商品与合计 14894 正常；`py_compile`、`ruff check` 通过。

## 2026-11-18 15:46

### 调整：两个 DEMO 启动前用 `batch_import` 预置 3 条数据

- `app`：`run()` 前导入 Meta80 × 2、鼠标 × 3、键盘 × 1。
- `app`：`run()` 前导入张三 / 李四 / 王五的三科成绩。
- 导入代码放在 `if __name__ == "__main__":` 里，模块被 import 时不产生副作用。
- 验证：以管道输入跑「查询 → 退出」，3 条数据、合计金额、人数与平均分输出正常；`py_compile`、`ruff check` 通过。

## 2026-11-18 15:44

### 功能：`ConsoleCrud` 新增批量导入 `batch_import`

- `import_many(rows, *, overwrite=False, validate=True) -> int`：一次写入多条记录，返回实际写入条数。
    - `rows` 支持 `{名称: 字段字典}` 或 `[(名称, 字段字典), ...]` 两种形式。
    - `overwrite=True` 时覆盖同名记录，默认跳过。
    - `validate=True`（默认）时校验字段与 `fields` 声明一致，缺字段的记录打印原因后跳过；
      字段声明为空时不校验。
    - 结束后打印一行汇总：成功 / 跳过 / 字段不符 条数。
- 验证：字典与列表导入、同名跳过、`overwrite` 覆盖、缺字段拦截、`validate=False` 放行，均实测通过；
  `py_compile`、`ruff check` 通过。

## 2026-11-18 15:26

### 功能：`app` 用 `ConsoleCrud` 实现学生管理系统

- 沿用文件头的案例说明，声明 `ConsoleCrud` 实例：三科成绩字段 `chinese` / `math` / `english`，均用 `read_float` 录入。
- `format_student`：单条展示姓名、各科成绩与总分（`{:g}` 去掉多余小数）。
- `summarize_students`：查询末尾追加人数与平均总分。
- 验证：空查询、添加、重复添加、修改、查询、删除不存在、删除、再查、退出全部分支模拟输入实测通过；
  `py_compile`、`ruff check` 通过。

## 2026-11-18 15:16

### 新增：`app` 演示 `ConsoleCrud` 组件

- 用购物车场景演示组件的三个可配置点：`fields`（`Field` 声明字段）、`format_row` / `summarize`（定制展示与合计）、
  `data`（传入初始商品数据）。
- 初始数据：Meta80 × 1、鼠标 × 2；金额展示保留两位小数。
- 验证：查询初始数据（合计 7397.00）、添加键盘后查询（合计 8294.00）、退出分支模拟输入实测通过；
  `py_compile`、`ruff check` 通过。

## 2026-11-18 15:14

### 重构：抽取控制台增删改查组件 `ConsoleCrud`

- 新增 `app`：把「菜单循环 + 嵌套字典增删改查 + 输入校验」收敛为一个可配置类。
    - `Field`：描述一个待录入字段（提示语 + 读取函数）。
    - `ConsoleCrud`：`add` / `update` / `delete` / `show` / `run` 通用流程；`read_str` / `read_float` / `read_int`
      静态方法提供输入校验；`format_row` / `summarize` / `empty_hint` 由使用方定制展示。
    - 提示语按 `entity` 拼接（如「商品已存在，请执行修改操作」），菜单按 `title` 渲染。
- `app`：删掉重复的 `read_float` / `read_int` / 各 CRUD 函数与菜单，改为声明一个
  `ConsoleCrud` 实例（字段 `price` / `num`，展示含小计与合计金额）。
- `app`：同样改为声明式配置（字段 `chinese` / `math` / `english`），补齐文件头说明。
- `app`：导出 `ConsoleCrud`、`Field`。
- 细微行为变化：学生管理新增/修改/删除后也会打印成功提示；提示语统一为中文逗号。
- 验证：两个 DEMO 的添加 / 重复添加 / 修改 / 修改不存在 / 删除 / 删除不存在 / 空查询 / 非法编号 / 退出
  全部分支模拟输入实测通过；`py_compile`、`ruff check` 通过。

## 2026-11-18 15:12

### 调整：`shopping_cart.py` 输入函数改为参数化提示语

- `read_price(tips)` / `read_num(tips)` 参考 `read_float` / `read_int` 的写法，把提示语改为入参，调用方传「商品价格：」「商品数量：」。
- 保留 `try/except ValueError`：参考写法把 `float()` / `int()` 放在 `try` 外，输入非数字会直接抛异常，这里仍按非法输入重试处理。
- 验证：非法价格、非法数量重试、添加、查询统计、修改、退出分支实测正常。

## 2026-11-18 15:10

### 调整：`shopping_cart.py` 输入函数对齐 `students_curd_demo.py`

- `read_price` / `read_num` 重命名为 `read_float` / `read_int`，实现与 `students_curd_demo.py` 中的同名函数保持一致：
  循环内直接 `float()` / `int()` 转换，单个 `if ... and ...` 判断，非法时打印提示后重试。
- `add_item` / `update_item` 调用处同步改为 `read_float("商品价格：")` / `read_int("商品数量：")`。
- 验证：`py_compile` 通过。

## 2026-11-18 15:05

### 功能：实现 `app` 购物车管理系统

- 在原有文档字符串与菜单基础上补齐实现：`add_item`、`update_item`、`delete_item`、`show_cart`，主循环用 `match case` 分发。
- 菜单标题由「学生管理系统」更正为「购物车系统」。
- `read_price` / `read_num` 用 `try/except ValueError` 包住 `float()` / `int()`：非数字、非正数都提示后重试，不再直接抛异常。
- 查询按「名称: xxx, 价格: xxx, 数量: xxx」输出，并追加小计与合计金额，覆盖需求中的「统计」。
- 验证：空购物车查询、添加、重复添加、修改、修改不存在、删除、删除不存在、非法编号、非法价格/数量、退出全部分支实测通过；
  `compileall` 通过。

## 2026-11-18 11:43

### 修改：`dict_demo.py` 删除 `Goods` TypedDict

- 移除 `class Goods(TypedDict)`，商品值改用字典字面量 `{"price": ..., "num": ...}`。
- 类型注解改为 `dict[str, dict[str, float | int]]`，比 `Any` 更精确，且不再需要导入 `typing`。
- 验证：主流程与查询统计输出正常；PyCharm 检查 0 error 0 warning。

## 2026-11-18 11:42

### 功能：实现 `app` 购物车管理系统（参考 Downloads/03字典案例.py）

- 用嵌套字典 `shopping_cart: dict[str, Goods]` 存储商品，`Goods` 用 `TypedDict` 描述 price/num。
- 按功能拆函数：`add_item`、`update_item`、`delete_item`、`show_cart`，主循环用 `match case` 分发。
- 补齐参考案例缺失的「删除购物车」分支（`pass` → 按 key `del`）。
- 查询在要求格式后追加小计与总金额，覆盖需求中的「统计」。
- 输入健壮性：抽出 `parse_price` / `parse_num` 返回 `Optional`，`read_float` / `read_num` 循环重试，非法数字与负数不再抛异常。
- 验证：添加/重复添加/修改/修改不存在/删除/删除不存在/非法编号/空购物车/非法数字 全部分支实测通过；PyCharm 检查 0 error 0
  warning。

## 2026-11-18 11:12

### 验证：本次改动涉及的 13 个 Python 文件全部运行通过

- 逐个执行并通过（exit=0）：`generic_type_demo.py`、`day8.py`、`lambda_typing.py`、`test.py`、`test1.py`、`tuple_demo.py`、
  `exec_time.py`、`hook.py`、`hook_old.py`、`log.py`、`args_kwargs_demo.py`（喂入模拟输入）。
- 修复：`test.py`、`test1.py` 直接运行报 `No module named 'lib'`，补上 `sys.path` 引导（`parents[2]` 指向项目根目录），与
  `lambda_typing.py` 一致，不再依赖 `PYTHONPATH=.`。
- `file_manager.py`、`file_manager_new.py` 为纯库文件，另做冒烟测试：写入、重复写入拦截、读取、搜索、删除、静态方法版均正常。
- 遗留：`test1.py` PyCharm 仍报两处「未使用 import」，对应代码已被注释，保留以备恢复。

## 2026-11-18 11:10

### 重构：全项目旧写法统一改为 Python 3.13 新语法

- `Callable` 从 `typing` 迁到 `collections.abc`（PEP 585）：`lambda_typing.py`、`file_manager.py`、`file_manager_new.py`、
  `hook.py`、`hook_old.py`、`log.py`。
- `log.py` 重写：`ParamSpec` / `TypeVar` 改为 `def log[**P, R](...)`，`extra` 改为元组，抽出 `_now()`，删除未使用的
  `HookCallback`。
- `args_kwargs_demo.py` 删除未使用的 `functools.wraps`、`typing.Any/Callable` 导入。
- `test1.py` 删除未使用的 `from os.path import join`。
- 复查范围：`app` 全部文件 + 根目录 `app/main.py`、`sitecustomize.py`，已无 `TypeVar(`、`ParamSpec(`、`Generic[`、`Optional[`、
  `Union[`、`from typing import Callable` 等旧写法。
- 验证：`python -m compileall lib` 通过；`log.py`、`hook.py` 运行输出正常；8 个改动文件 PyCharm 检查无 error（`test1.py`
  仅剩两处因代码被注释而未使用 import 的既有警告）。

## 2026-11-18 11:07

### 优化：`app` 改用 Python 3.13 新语法

- 模块级 `P = ParamSpec("P")`、`R = TypeVar("R")` 改为函数级类型参数 `def hook[**P, R](...)`。
- `type` 语句定义 `HookCallback`、`HookExtra` 别名，`HookExtra` 明确为 `tuple[str, str]`。
- `extra` 由可变 `list` 改为元组，避免回调侧误改后影响后续调用。
- 抽出 `_now()` 去重 `on_before` / `on_after` 里的时间格式化。
- 回调判空由 `if before:` 改为 `if before is not None:`，避免误判假值可调用对象。
- 验证：脚本输出正常；PyCharm 检查无 error/warning。

## 2026-11-18 11:05

### 重构：`generic_type_demo.py` 改用 Python 3.13 新语法并清理演示代码

- 删除 5 个模块级 `TypeVar`（`Int`/`Float`/`Bool`/`List`/`Dict` 还遮蔽了内置名）以及未使用的 `T`。
- 用 PEP 695 约束类型参数 `def echo[X: (int, str)](value: X) -> X` 保留「受约束类型参数」这一知识点。
- `__getitem__` 返回类型改为 `T | Self`，消除前向引用，随之删掉 `from __future__ import annotations`。
- 演示代码收进 `main()` 并用 `if __name__ == "__main__"` 守卫，模块可安全导入（此前 import 会直接打印一堆结果）。
- 修正因数据换成 `range(20)` 而失真的输出注释。
- 验证：运行输出正确；PyCharm 检查无 error/warning；`typing.get_type_hints` 解析为 `Union[T, Self]`。

## 2026-11-18 10:50

### 补充：`Box` 切片步长验证与演示

- 结论：步长无需改代码。`nums[0:4:2]` 的 `step` 存放在 Python 传入的 `slice` 对象里，现有实现转发给底层序列后天然生效。
- 文档字符串补充 `nums[1:4:2]` 说明，新增演示 `nums[0:4:2]` → `Box([10, 30])`、`nums[::-1]` → 倒序。

## 2026-11-18 10:47

### 修复：`Box.__getitem__` 注解触发「前向引用联合体需整体加引号」

- 现象：`-> T | "Box[T]"` 只有一半加引号，PyCharm 报「具有前向引用的联合体类型注解必须完全用引号括起来」。
- 解法：文件顶部加 `from __future__ import annotations`（与 `app`
  一致），注解整体延迟求值，前向引用无需加引号；同时去掉内层冗余引号，改为 `-> T | Box[T]`。
- 验证：脚本正常运行；`typing.get_type_hints(Box.__getitem__)` 可解析为 `int | slice` 与 `Union[~T, Box[~T]]`。

## 2026-11-18 10:45

### 功能：`Box` 支持下标取值与切片

- 新增 `__getitem__`：`nums[0]` 返回单个元素，`nums[1:3]` 返回新的 `Box`（包装切片结果）。
- 新增 `__repr__`，打印实例时显示 `Box([20, 30])` 而不是对象地址。
- 局限：T 必须自身可下标（list/tuple/str），`Box(42)[0]` 会 TypeError。
- 验证：输出 `10 40`、`Box([20, 30])`、`Box('el')`。

## 2026-11-18 10:43

### 修复：`app` 两处 TypeVar 误用

- 第 13 行 `e["name"]` 对 `TypeVar` 对象取下标，报 `TypeError: 'typing.TypeVar' object is not subscriptable`；改为打印
  `(e.__name__, e.__constraints__)`。
- `class Box([T])` 把列表字面量当基类，报 `TypeError: list expected at most 1 argument, got 3`；改为
  `class Box(Generic[T])` 并导入 `Generic`。
- 修正复制粘贴导致的约束错误：`Float` 用 `float`、`Bool` 用 `bool`、`Dict` 用 `dict`（原先三者都是 `int`）。
- 补 `print(box.get(), box2.get())` 便于观察实例化结果。
- 验证：`python lib/page/generic_type_demo.py` 输出约束列表与 `42 hello`。

## 2026-11-18 09:35

### 文档：新增 `docs/Python-Literal类型.md` 说明 `Literal[...]`

- 概念、语法约束（只能写字面量）、与 `str` 的区别。
- 以 `app`、`app` 的实际签名为例。
- 运行时是否生效（Pydantic/FastAPI 会校验，普通函数需手写判断）。
- `Literal` 与 `Enum` 的选型对比，以及与 `LiteralString` 的区别。

## 2026-11-18 09:26

### 修复：`app` 列表推导式 `NameError`

- `[(i, e) for e in enumerate(person)]` 只解包了元组 `e`，`i` 从未赋值，运行即报 `NameError: name 'i' is not defined`。
- 改为 `[(i, e) for i, e in enumerate(person)]`，注释同步为真实输出 `[(0, '张三'), (1, 25), (2, 1.75)]`。
- 验证：`python lib/page/tuple_demo.py` 正常输出，无报错。

## 2026-11-18 08:52

### 清理：删除残留的旧克隆目录 `/Users/shang/GitHub/python_templet_project`

- 该目录已不是 Git 仓库，仅剩一个 479M 的 `.venv`，无源码、无提交历史，删掉不丢代码。
- 删除前确认：无进程占用、本项目代码/配置均未引用该路径（仅 CHANGELOG 与 docs 中作为举例提到）。
- 已执行 `rm -rf`，目录不存在；`.venv` 相关环境变量残留需在终端 `deactivate` 解决。

## 2026-11-18 08:51

### 修复：`.venv` 从旧工程拷贝导致所有命令行脚本指向错误解释器

- 现象：`uv run fastapi deploy` 报 `To use the fastapi command, please install "fastapi[standard]"`，堆栈指向
  `/Users/shang/GitHub/python_templet_project/.venv`。
- 根因：本项目 `.venv` 是从 GitHub 那份工程整体拷贝的，`.venv/bin` 下 41 个脚本有 33 个 shebang 仍指向旧路径（`uvicorn`、
  `streamlit`、`fastapi` 均中招）；`.venv/bin/python` 是二进制启动器不受影响，所以此前没暴露。venv 不可搬迁。
- 修复：`rm -rf .venv && uv sync` 重建，脚本 shebang 全部指向本项目，旧路径残留 0 个。
- 依赖：`uv add "fastapi[standard]"`，`pyproject.toml` 改为 `fastapi[standard]>=0.162.0`，新增 fastapi-cli、watchfiles、httpx
  等 14 个包，从而可用 `fastapi dev` / `fastapi run`。
- 澄清：`fastapi deploy` 是部署到 FastAPI Cloud 的命令，本地开发不用它。
- README 补充 `fastapi dev` 启动方式，并注明必须带 `PYTHONPATH=.`，否则报 `No module named 'lib'`（已实测）。

## 2026-11-17 21:28

### 提交：按功能拆分本次改动为 5 个提交

- `chore(依赖)`：删除 requirements.txt，补充 python-dotenv。
- `refactor(结构)`：六个目录迁入 `app` 并统一 `lib` 包导入（59 个文件）。
- `feat(图书API)`：新增 `app` 与 README 启动说明。
- `chore(作业)`：新增 day9–day11 空白占位文件。
- `docs(变更日志)`：更新 CHANGELOG。

## 2026-11-17 21:27

### 重命名：`app` → `app`

- 文件在提交前直接以 `app` 入库，仓库历史中不出现 `book_api.py`。
- README 启动命令同步改为 `PYTHONPATH=. .venv/bin/uvicorn lib.api.book:app --host 127.0.0.1 --port 8001 --reload`。
- 清理 `app` 中残留的 `book_api` 字节码缓存。

## 2026-11-17 21:22

### 文档：README 增加停止 FastAPI 服务的命令

- 前台运行：提示按 `Ctrl+C` 停止。
- 后台运行：新增 `lsof -ti :8001 | xargs kill`，按端口结束进程。

## 2026-11-17 21:21

### 文档：README 增加 FastAPI 服务的启动命令

- 新增 `PYTHONPATH=. .venv/bin/uvicorn lib.api.book_api:app --host 127.0.0.1 --port 8001 --reload`。
- 补充接口文档地址 `/docs`、三个接口说明（`/`、`/books`、`/books/count`）以及端口冲突时用 `--port` 换端口的提示。

## 2026-11-17 21:20

### 修复并启动：`app` FastAPI 图书查询服务

- 导入改为 `from lib.model.book import Book`，修复迁移后的 `ModuleNotFoundError: No module named 'model'`。
- 移除 `authlib.common.encoding.json_dumps`：它本质是 `json.dumps`，无法序列化 Pydantic `Book`，且返回字符串会被 FastAPI
  再包一层 JSON（前端拿到转义字符串）。
- 改为直接返回 `dict` / `list[Book]`，由 FastAPI + Pydantic 完成序列化。
- `@app.get("book/count")` 补上开头的 `/` 并调整为 `/books/count`，否则 FastAPI 导入时断言失败。
- 启动命令：`PYTHONPATH=. .venv/bin/uvicorn lib.api.book_api:app --host 127.0.0.1 --port 8001 --reload`（8000 被另一项目
  `ecommerce-rag` 占用）。
- 验证：`/` 返回欢迎语、`/books` 返回 3 本图书、`/books/count` 返回 `{"total":20}`，`/docs` 可访问。

## 2026-11-17 21:05

### 清理：删除已废弃的 `requirements.txt`

- 原内容仅 `requests`、`ipython`、`pytest`、`black` 四项，全项目无任何代码导入，`pyproject.toml` 也未列出。
- 项目依赖已完全由 uv 管理（`pyproject.toml` + `uv.lock`）：`requests` 由其他库间接引入，`ipython` / `pytest` / `black`
  不在锁文件中；`black` 的职责由 Ruff 取代。
- 无文档、脚本或 CI 引用该文件，删除后不影响运行。
- 若后续需要 pytest，建议使用 `uv add --dev pytest` 写入 `[dependency-groups]`，而不是恢复 requirements 文件。

## 2026-11-17 21:03

### 重构：把 `assets`、`enums`、`base_widget`、`model`、`page`、`util` 六个目录整体移入 `app`

- 目录迁移：`git mv assets|enums|base_widget|model|page|util lib/`，历史记录保持为 rename。
- 导入统一改为 `lib` 包前缀：`from lib.util.dlog import DLog`、`from lib.model.book import Book`、
  `from lib.page.homework.section1.day1 import log_poetry` 等，共涉及 `base_widget`、`model`、`util`、`page` 下 15 个文件。
- 脚本 `sys.path` 引导改为 `parents[2]`（指向项目根目录）；`page/io/file_demo.py` 的资源根变量改名为 `resource_root`（指向
  `app`）。
- 资源路径：`model/book_library_model.py` 的 `parent.parent` 自然指向 `app`，`books.json` 路径保持有效；`page/student.py`
  的 `SCORE_PATH` 改为 `project_root / "lib" / "assets" / ...`。
- 配置与文档同步：`README.md`、`docs/PyCharm-Streamlit外部工具配置.md`、`docs/Python-Callable与code属性.md`、
  `tools/pycharm-streamlit-runner` 的说明与命令改为 `app`；`.gitignore` 的 AI 机器人运行数据路径改为
  `app`。
- 未改动：`page/ai_robot/app.py` 仍使用同目录扁平导入（Streamlit 会把脚本目录加入 `sys.path`），可正常启动。
- 验证：`python -m compileall lib` 通过；`lib` 下模块导入正常（`lib.page.test1` 会执行交互输入、`lib.page.codable` 存在既有的
  `WeekdayEnum.valueOf` 报错，故不以导入结果为准）；`PYTHONPATH=. python lib/page/student.py`、从其他目录运行
  `app` 均能正确定位模块与资源；Ruff 仅剩迁移前已存在的告警。

## 2026-11-17 20:49

### 变更：`Book` 彻底取代 `BookModel`

- `model/book.py` 的 `Book` 合并 `BookModel` 全部字段：`id / title / author / isbn / price / stock / is_borrow`；原来的
  `name` 更名为 `title`，与 `books.json` 及页面里的 `book.title` 对齐。
- 默认值：`id=0`、`price=0.0`、`stock=0`、`is_borrow=False`。`books.json` 只有 `title/author/isbn/industry`，缺省字段自动取默认值，
  `load_books()` 不再报 `ValidationError`。
- 唯一标识回到 `isbn`：`__eq__` / `__lt__` 按 `isbn` 比较，`list.index()` 和 `remove_book()` 可直接用 ISBN 定位；`id`
  降级为辅助字段。
- `model/book_library_model.py` 中 7 处 `BookModel` 替换为 `Book`，导入改为 `from model.book import Book`。
- 删除 `model/book_model.py`（已无任何引用）。
- 验证：载入 10 本书、首本默认值正确、借书/还书、同 ISBN 相等、按 ISBN 排序、`index()` 定位均正常；`ruff check` 通过；
  `PYTHONPATH=. python page/data_type_test.py` 输出正常。
- 遗留：`borrow_book()` 不判断 `is_borrow`，已借出的书再次借仍返回 `True`（页面在调用前已自行判断），本次未改动。

## 2026-11-17 20:47

### 变更：`BookModel` 的属性方法合并到 `Book`

- `model/book.py` 的 `Book` 增加四个方法：`from_dict`（`model_validate` 的封装）、`__str__`、`__eq__`、`__lt__`。
- 唯一标识从 `BookModel.isbn` 换成 `Book.id`：`__eq__` / `__lt__` 均按 `id` 比较，排序可直接 `sorted(books)`。
- `__str__` 改为输出 `id / name / author / price / stock`，与 `Book` 字段对齐。
- 未合并字段：`BookModel` 的 `isbn`、`is_borrow` 在 `Book` 中没有对应字段，`book_library_model.py` 仍依赖它们，故保留
  `book_model.py` 不动。
- 验证：`from_dict` 字符串价格 `"59.9"` 自动转 `float`、同 id 相等、不同 id 排序正确、非法价格抛 `ValidationError`；
  `ruff check` 通过。

## 2026-11-17 20:22

### 修复：`FileManager.write` 的重复检测失效（文件里有记录却查不到）

- 现象：`contacts.txt` 中已有 `北辰|11111111111|beichen@qq.com`，`row in lines` 仍判定为不存在，同一联系人可被重复写入。
- 根因：`open("a+")` 的 **读指针初始在文件末尾**（追加模式的语义），此时 `f.readlines()` 返回 `[]`，`row in lines` 永远是
  `False`，去重检查形同虚设。
- 修复：`open("a+")` 之后先 `f.seek(0)` 再 `readlines()`；写操作不受影响，`a+` 的写入仍固定追加到末尾。
- 验证：临时文件先写一条，重复写返回 `False`、新联系人返回 `True`，文件内容与预期一致。
- 遗留：`print(["write", row, lines])` 调试输出仍在 `write()` 中，未擅自删除。

## 2026-11-17 20:09

### 修复：`day7.1.py` 里 `@hook()` 报「`'module' object is not callable`」

- 根因：`from util import hook` 导入的是 **`util/hook.py` 模块**，不是模块里的 `hook` 装饰器函数；对模块加括号 `hook()`
  自然不可调用。
- 修复：改为 `from util.hook import hook`，从模块内部导入函数。
- 验证：`py_compile` 通过；`@hook()` 装饰的函数可正常调用并返回结果。

## 2026-11-17 19:45

### 新增：保存时自动格式化（Ruff），对齐 Android Studio 的 ⌘S 行为

- `pyproject.toml` 增加 `[tool.ruff]`：`line-length = 120`、`target-version = "py313"`；`[tool.ruff.lint]` 选 `E` / `F` /
  `I`。
- 格式化器定为 Ruff（`~/.local/bin/ruff` 0.15.10），不用 Black（当前未安装）。
- 存量文件 **不做**批量重排，只对之后保存的文件生效，避免大面积 diff。
- PyCharm 侧的两个勾选（Actions on Save → Reformat code、Python → Formatter → Ruff）需在 GUI 里点选，运行中的 IDE
  会覆盖对配置文件的直接修改，故未代改。

## 2026-11-17 18:18

### 新增全局 skill：`python-indent`（修改 Python 代码保持正确缩进）

- 规则：改 Python 代码时缩进必须正确且沿用文件原有风格，文件编辑、终端 heredoc / `python -c` / REPL 输入、回复中的代码块都适用。
- 真源：`~/.agents/skills/python-indent/SKILL.md`，含动手前确认基线、层级铁律（同一逻辑块同级）、终端输入要求、改完验证（
  `py_compile` / `ruff`）四部分。
- 同步：用 `install-global-skill` 脚本建相对软链，`.claude` / `.cursor` / `.qwen` 等 48 个 agent 目录全部 `LINK`，`status`
  返回 0；`~/.claude/skills/python-indent` 已可在本会话识别。

## 2026-11-17 18:14

### 修复：`file_manager.py` 的 `update()` 中 `lines[idx] = search_cb(key, lines)` 的类型警告与逻辑错误

- 警告根因：`search_cb` 类型是 `Callable | None`，在 `if` 之外第二次调用类型检查器无法确认非 None（`None is not callable`
  ）；同时 `search_cb(...)` 返回 `list[str]`，赋给单个元素 `lines[idx]`（`str`）类型不匹配。
- 逻辑问题：原实现把匹配列表塞进一个元素；`f.writelines()` 却在只读的 `"r"` 模式句柄上调用，运行时会抛
  `io.UnsupportedOperation`；`return True` 写在 `except` 之后，失败也返回成功；`update_cb` 参数完全未使用。
- 修复：读和写拆成两个 `with`；`targets` 复用第一次搜索结果，不再重复调用 `search_cb`；`update_cb(key, targets)`
  返回新行列表，用切片赋值 `lines[idx:idx + 1] = new_rows` 替换（一行换多行也支持）；未传回调则原样保留；成功与各失败分支分别
  `return`，异常文案改为「更新失败」。
- 顺带：删除 IDE 自动补的未使用导入 `Any` / `ParamSpec` / `TypeVar` / `cast`。
- 验证：临时副本测了单行替换、一行换多行、关键字未命中、文件不存在四种情况，结果均符合预期；`ruff check` 全通过，`mypy` 无问题。

## 2026-11-17 18:07

### 修复：`file_manager.py` 的 `update()` 里调用 `search()` 报错

- 两处根因：
    1. `from re import search` 是 IDE 自动补的导入，`search(path=..., key=..., cb=...)` 实际调用的是 `re.search`，会抛
       `TypeError: unexpected keyword argument 'path'`；即使删掉该导入，直接写 `search(...)` 也会 `NameError`
       ——静态方法之间调用必须写类名 `FileManager.search(...)`，方法体不查类命名空间。
    2. 变量名拼写 `targts` → `targets`。
- 修复：删除 `from re import search` 与无关的 `from enum import Flag`；调用改为
  `targets = FileManager.search(path=path, key=key, cb=cb)`。
- 遗留：`Any` / `ParamSpec` / `TypeVar` / `cast` 导入未使用（`ruff` F401），未擅自删除；`update()` 目前只取了搜索结果，写回逻辑尚未补。
- 验证：对 `contacts.txt` 调用 `FileManager.update(path=..., key="张三")` 无异常；`search` 按关键字返回 2 条匹配行。

## 2026-11-17 18:00

### 按功能拆分提交：本轮改动整理为 6 个提交

- `docs(学习笔记)`：`python-del-usage.md` 扩充对比表、新增 `python-callable-code-attr.md`。
- `docs(学习笔记)`：新增 `orm-default-values.md`。
- `refactor(日志工具)`：`hook.py` 引入 `ParamSpec` / `TypeVar` 保留被装饰函数签名，旧实现注释留档到 `hook_old.py`。
- `feat(通讯录)`：新增 `util/file_manager.py`，`day7.1.py` 改为调用该类，姓名匹配抽为 `match_name`。
- `refactor(作业)`：`day7.py` 中 `Salesman` 重命名为 `Seller`。
- `feat(练习)`：新增 `tuple_demo.py` / `args_kwargs_demo.py`，`date_demo.py` 增加毫秒时间函数，`day5` / `day6` / `day8`
  补充练习。
- `page/homework/section1/contacts.txt` 为通讯录运行产生的测试数据，未纳入本次提交。

## 2026-11-17 17:05

### 修复：`day8.py` 中 `avg(list(e[-3:]))` 把变量当函数调用

- 报错：`TypeError: 'float' object is not callable`。
- 根因：`handle()` 循环里 `avg = total / 3` 把 `avg` 绑定成了 **float 变量**，后面再写 `avg(...)` 等于给浮点数加括号调用；而且原来的
  `avg` 从头到尾都不是函数。
- 修复：新增模块级辅助函数 `avg_score(scores)`（`sum(scores) / len(scores)`），列表推导改为 `avg_score(e[-3:])`；循环里的局部变量改名为
  `average`，避免遮蔽（shadow）同名函数。
- 顺带：去掉多余的 `list(...)`——`e[-3:]` 在元组上切片本就返回元组，`sum()` 可直接处理；保留转换只是多建一个对象。
- 验证：运行输出 `better_list` 为李慕婉、周轶、红蝶、许木 4 人，与手算一致。

## 2026-11-17 16:29

### 修复：`day7.1.py` 中 `add_contact_new()` 报 TypeError

- 报错：`add_contact_new() missing 3 required positional arguments: 'name', 'phone', and 'email'`。
- 根因：函数签名 `def add_contact_new(name: str | None, phone: str | None, email: str | None)` 只有类型注解、没有默认值，三个参数都是
  **必填位置参数**；`str | None` 只是"允许传 None"，并不会让你省略实参。因此无参调用必然报 TypeError。
- 修复：三个参数补上默认值 `= None`，与函数体内 `name or input(...)` 的兜底写法对齐。
- 验证：`printf` 管道喂入三个值跑脚本，输出 `王五,13800138003,wangwu@example.com`，无异常。

## 2026-11-17 16:06

### 调整：`day7.1.py` 的 `del_contact` 改用 `with` 上下文管理器

- 按作业要求（「使用 with 上下文管理器操作文件」）重写：读用 `with path.open("r", encoding="utf-8")`，写用
  `with path.open("w", encoding="utf-8")`，两次 with 各管一段。
- 语义不变：全量读到内存 → 内存删第一条匹配 → `"w"` 模式整体覆盖写回。
- 异常分支拆开：`FileNotFoundError` 提示「暂无联系人」，其余 `OSError` 提示删除失败，读失败后直接 return，不再往下走。
- 验证：mock `input` 跑三行测试数据，删除 `SD的` 后文件为 `'张三|...\n李四|...\n'`；未命中关键字打印「未找到包含「不存在」的联系人」。
- 遗留：`exceptiongroup.catch`、`streamlit.user_info`、`typing.Any` 三个导入未使用（`ruff` F401 ×3），未擅自删除。

## 2026-11-17 15:55

### 修复：`day7.1.py` 删除联系人「提示成功但数据还在」

- 根因：`open("r+")` 下 `readlines()` 读完后指针停在文件末尾，`writelines(lines)` 从末尾开始写等于 **追加**；文件只有一行时
  `lines` 删完为空，`writelines([])` 什么都不写，文件原封不动。随后 `readlines()` 从末尾读自然得到 `[]`
  ，造成"删除成功"的假象。多行场景下问题更严重——剩余行会被追加到文件末尾，内容翻倍（`r+` 覆盖写需要 `seek(0)` + 写 +
  `truncate()` 三步）。
- 修复：`del_contact` 改为「`read_text` 全量读 → 内存删 → `write_text` 整体重写」；`splitlines(keepends=True)` 保留换行，写回
  `"".join(...)`；先判断 `targets` 为空，避免 `IndexError`；`FileNotFoundError` 单独提示"暂无联系人"。
- 顺带：`search_contact` 的 `open("a")` 改为 `open("r")`（原写法 `readlines()` 会抛 `not readable`）；`show_all_contacts` 的
  `r+` 改为 `r`。
- 验证：mock `input` 跑 `del_contact`，测试数据三行含 `SD的`，删除后文件为 `'张三|...\n李四|...\n'`，`SD的` 行确实消失。

## 2026-11-17 12:07

### 扩充：`docs/Python-del用法.md` 增加第八节「`del` 与各类容器的移除方法对照」

- 总览表覆盖 `list` / `dict` / `set` / `frozenset` / `str` / `tuple` / `deque` / `array.array`
  ：按位置删、按值删、弹栈取回、清空、删名字五种操作各自能否用 `del` 或哪种方法。
- 记录三条硬性限制的实测报错：`'set' object doesn't support item deletion`、str、tuple 同理——只有有序可变序列支持
  `del 容器[i]`。
- 分类型给出用法：dict 的 `del` / `pop` / `pop(k, 默认)` / `popitem()`（3.7+ LIFO）分工；set 的 `remove`（KeyError）vs
  `discard`（静默）vs `pop`（随机）；str/tuple 用切片重建且 `del s` 只删名字；deque 的 `popleft` O (1) 对比 `list.pop(0)` O
  (n)；array 语法同 list。
- 新增「容易混的几点」表：同名不同异常（list.remove → ValueError / set.remove → KeyError）、`dict.pop()` 空参报 TypeError、
  `clear()` 与 `del x[:]` / `del x` 的区别、只有 `del` 支持切片步长。
- 新增复杂度对照表（尾部 pop O (1)、`del lst[i]` O (n-i)、deque 两端 O (1)、dict/set 平均 O (1)）。
- 全部结论均用 Python 3.13.2 实测核对。

## 2026-11-17 12:05

### 扩充：`docs/Python-del用法.md` 增加「`del` 与 `remove` 的完整对比」

- 新增对比表：定位方式、语句 vs 方法、返回值、找不到时的异常（`IndexError` / `ValueError`）、重复元素只删第一个、切片批量、时间复杂度、负数索引、是否原地修改。
- 记录三个坑：`remove` 用 `==` 比较导致 `float("nan")` 删不掉（CPython 有身份捷径，同一对象才能命中）；`remove`
  只删第一个，删全部应用推导式；遍历中 `del`/`remove` 都会因下标前移而漏删。
- 补充「怎么选」对照表与「都是原地修改」示例（`a is b` 仍为 `True`，区别于推导式重建）。
- 第六节「不能在遍历中删除」的列表示例与新增坑 3 重复，改为指向上文；文末速查表补「按值删列表元素」一行。

## 2026-11-17 11:49

### 优化：`util/hook.py` 用 `ParamSpec` / `TypeVar` 保留被装饰函数的签名与返回类型

- `hook` 返回类型由 `Callable[..., Callable[..., Any]]` 改为 `Callable[[Callable[P, R]], Callable[P, R]]`；`decorator`
  改为接收 `Callable[P, R]`、返回 `Callable[P, R]`；`wrapper` 改为 `(*args: P.args, **kwargs: P.kwargs) -> R`。
- 拿 `__code__` 处改为 `cast(FunctionType, func).__code__`：`Callable` 不保证有 `__code__`，收窄后才能通过类型检查。
- 新增 `HookCallback = Callable[..., None]` 别名，三个回调参数共用。
- `filename` 改用 `Path(code.co_filename).stem`，替代 `split("/")[-1]` + `split(".")[0]`，Windows 路径与带点文件名都正确。
- `extra` 显式注解 `list[str]`；`except Exception as e` 改为 `except Exception`（原 `e` 未使用）。
- 验证：`python3 util/hook.py` 输出正常（`hook.add ... Line:68`）；`ruff check` 通过；`uvx mypy util/hook.py` 无问题；mypy
  `reveal_type(add)` 为 `def (a: int, b: int) -> int`，`add("1", 2)` 正确报 `arg-type`；PyCharm 文件检查无任何问题。

## 2026-11-17 11:02

### 新增：`docs/Python-Callable与code属性.md`，整理 `Callable` 上找不到 `__code__` 的来龙去脉

- 记录报错现象、根因（`Callable` 只承诺 `__call__`，`__code__` 是 `types.FunctionType` 专有属性）。
- 列出对比表：`def` 函数 / `lambda` / `functools.partial` / 可调用实例 / 类 / 内置函数，各自是否 `Callable`、是否有
  `__code__`。
- 两种修法：注解收窄为 `types.FunctionType`（推荐）、保留 `Callable` 用 `cast`（附 `getattr` 兜底写法）。
- 补充「装饰器取函数信息」的 inspect 对照表（`getsourcefile`、`signature`、`stack` 等）及各自失效场景。

## 2026-11-17 10:53

### 修复：`util/hook.py` 中 `func.__code__` 报「在 (...) -> Any 中找不到引用 `__code__`」

- 现象：`decorator(func: Callable[..., Any])` 内部访问 `func.__code__`，PyCharm/类型检查器报属性不存在。
- 根因：`Callable[..., Any]` 只声明「可调用」，仅保证 `__call__`，不保证具有 `__code__`；`__code__` 是普通函数（
  `types.FunctionType`）专有属性，类、`functools.partial`、可调用实例都没有。
- 修复：`decorator` 的参数注解由 `Callable[..., Any]` 改为 `types.FunctionType`，返回类型仍为 `Callable[..., Any]`
  ；装饰器本就只支持真正的函数，语义更准确。
- 验证：`python3 util/hook.py` 输出 `[before add ...]` / `[after add ...]: 3` / `3` 不变；PyCharm 检查该报错消失，仅剩 4
  条「局部变量未使用」弱警告（`filename`、`lineno`、`func_name`、`e`）。

## 2026-11-16 20:18

### 新增：`docs/ORM字段默认值.md`，整理各 ORM 字段默认值写法

- 按框架给出 `default=` 示例：SQLAlchemy 2.0（`mapped_column`）、SQLModel/Pydantic（`Field`）、Django、Peewee，并补充普通类参数默认值与
  dataclass `field(default_factory=...)` 的对照。
- 梳理 `default`、`default_factory`、`server_default`、`db_default` 的区别与适用场景。
- 记录两个坑：默认值生效时机因框架而异（SQLAlchemy 普通映射在 flush 时才补值）；可变默认值不能直接写 `[]`/`{}`，要用 `list` 或
  `default_factory`。
- 补充普通类改造成 ORM 模型时的迁移要点。

## 2026-11-16 16:13

### 修复：`filter_data` 把 `**kwargs` 注解成 `dict[str, Any]` 导致的类型警告

- 警告现象：四个配置项赋值处报「应为类型 int/bool/str，但实际为 `dict[str, Any] | int`」，两个调用处每个关键字实参都报「应为
  `dict[str, Any]`」。
- 根因：`**kwargs: X` 注解的是 **每个关键字参数的值类型**，不是整个 kwargs 的类型。写成 `dict[str, Any]` 等于声明「每个值都是字典」。
- 修复：签名改为 `**kwargs: Any`（值类型为 Any），局部注解保持不变；调用处与 `.get()` 处警告全部消失。
- 验证：`ruff check` 通过；PyCharm 仅剩 `goods_total_amount` 原有的 `price_sum_new` 弱警告；两组用例输出 `[9, 8, 7, 5]`、
  `[1, 3, 5]` 不变。

## 2026-11-16 16:07

### 修复：`filter_data` 四个配置项赋值处的类型不匹配警告

- 保留「带默认值的局部注解」写法：`threshold: int = kwargs.get("threshold", 1)` 等四行不变。
- 把签名中的 `**kwargs: int | str | bool` 改为 `**kwargs: Any`：原联合类型里每个键实际类型不同，逐个赋给 `int`/`bool`/
  `str` 时 PyCharm 报「应为类型 X，但实际为 int | str | bool」共 4 条。
- 清理遗留的 `cast` 未使用导入；`if unique is True` 已简化为 `if unique`。
- 验证：`ruff check` 全部通过；PyCharm 仅剩 `goods_total_amount` 原有的 `price_sum_new` 弱警告；两组用例输出
  `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:40

### 调整：`filter_data` 的过滤恢复为 `filter` + `lambda` 写法

- 把列表推导式改回 `list(filter(lambda x: x >= limit, items))`，并在分支内用 `limit: int = threshold` 显式收窄：lambda 会捕获
  `limit`（已声明为 `int`），不再把 `threshold` 推断成含 `None` 的联合类型。
- 行为与推导式版本完全一致；PyCharm 该行警告消除，`ruff check` 通过。
- 验证：两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:38

### 修复：`page/homework/section1/day5.py` 中 `filter_data` 的 `None` 比较警告

- 警告内容：`'int | str | bool | None' 的成员 'None' 没有特性 '__le__'`。根因是 `**kwargs: int | str | bool`
  把所有配置值混成一个联合类型，`kwargs.get("threshold", None)` 再叠加 `None`，PyCharm 无法在 lambda 闭包里把 `threshold`
  收窄成数值。
- 新增 `FilterOptions(TypedDict, total=False)` 精确描述四个配置项类型，函数签名改为 `**kwargs: Unpack[FilterOptions]`，
  `.get("threshold")` 的类型变为 `int | None`。
- 过滤改用列表推导式，并在分支内用 `limit: int = threshold` 显式收窄类型，消除闭包类型推断问题；行为与原 `filter` 写法一致。
- 验证：`ruff check` 全部通过；PyCharm 检查该文件仅剩 `goods_total_amount` 里原有的 `price_sum_new` 未使用弱警告；
  `filter_data` 两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:10

### 修复：`page/homework/section1/day5.py` 中 `analyze_scores` 的 IDE 警告

- 删除误导入且未使用的 `from itertools import count`：它导致 `goods_total_amount` 和 `analyze_scores` 里的局部变量
  `count` 被判为「隐藏外部作用域名称」（ruff F401/F811，PyCharm weak warning）。
- 三个配置项改用 `kwargs.get(key, 默认值)`：原写法 `pass_line` 取值时误判 `show_detail is not None`，且 `kwargs.get()`
  可能返回 `None`，PyCharm 报「`Literal[60] | None | Any` 的成员 `None` 没有 `__le__`」以及 `round()` 实参不匹配。
- 按题目要求补全类型注解：`*args: float`、`**kwargs: Any`、返回 `dict[str, int | float | str]`，并修正空分数分支的缩进。
- 验证：`ruff check` 全部通过；PyCharm 检查 `analyze_scores` 已无警告；脚本运行输出 `report1`、`report2` 与预期数值一致。

## 2026-11-16 11:19

### 调整：`page/date_demo.py` 改为不封装函数，直接演示底层 API

- 按要求去掉全部函数定义，改为顺序脚本：每段先调用 API 再打印结果，读者可以直接看到输入与输出。
- 保留 10 个演示段：字符串→datetime、datetime→字符串、datetime→时间戳、时间戳→datetime（本地/UTC）、字符串→时间戳、时间戳→字符串、往返断言、带
  `%z` 的时区字符串、`fromisoformat`、当前时间三形态（秒/毫秒时间戳）。
- 验证：`.venv/bin/python page/date_demo.py` 退出码 0，输出与封装版一致，往返断言通过。

## 2026-11-16 11:13

### 新增：`page/date_demo.py`，字符串 / datetime / 时间戳三种时间形态互转

- 提供 6 个函数：`str_to_datetime`、`datetime_to_str`、`datetime_to_timestamp`、`timestamp_to_datetime`、`str_to_timestamp`、
  `timestamp_to_str`，覆盖字符串 ⇄ datetime ⇄ 时间戳的全部方向，统一使用 `DEFAULT_FMT = "%Y-%m-%d %H:%M:%S"`。
- 演示带时区场景：`fmt` 加 `%z` 才能保留时区；`fromtimestamp(tz=timezone.utc)` 返回 aware 时间；ISO 字符串可直接用
  `datetime.fromisoformat`（3.11+ 支持末尾 `Z`）。
- 注释说明 naive datetime 调用 `timestamp()` 时按本地时区解释，跨时区计算应显式传 `tz`。
- 验证：`.venv/bin/python page/date_demo.py` 退出码 0，字符串往返、timestamp 往返、带时区字符串往返断言全部通过，本地时间输出
  `2026-11-16 10:57:00`。

## 2026-11-16 10:57

### 修复：`page/homework/section1/day5.py` 的 `second2date` 秒数换算

- 保持原有「年/月/日 时:分:秒」的换算结构（365 天/年、30 天/月的近似口径），改用 `divmod` 逐级取商和余数。
- 修复三处错误：`/` 真除法导致 年/月/日/时/分 全是浮点数；`v % year` 对浮点数取模得到的是无意义的零头，应使用上一级的余数；
  `hour = v / 3600` 未扣除整天的秒数。
- 分/秒改为 `:02d` 补零，函数补上 `-> str` 返回类型注解。
- 移除误导入的 `from unittest import result`。
- 验证：时间戳 `1794797837` → `56:11:3 02:57:17`；`3725` → `0:0:0 01:02:05`；`86400` → `0:0:1 00:00:00`，均与预期一致。

## 2026-11-16 10:19

### 新增：`docs/Python-del用法.md`，整理 Python `del` 的使用场景

- 按场景分七节：删除变量绑定、列表元素（索引/切片/清空）、字典键、对象/类属性、导入名、遍历中删除的陷阱、函数内删全局名。
- 补充 `del lst[i]` / `remove` / `pop` / `clear` / `del lst` 的对比表，以及 `del lst[:]` 保留容器对象、`del lst` 只删名字的区别。
- 指出遍历中删除会抛 `RuntimeError`（字典）或漏删（列表），给出 `list(d)` 快照和推导式重建两种正确做法。
- 关联图书管理系统 `day4.py` 的场景：删除图书应写 `del books[book_name]`，不要用 `books[book_name] = None`。

## 2026-11-15 17:26

### 新增：`page/homework/section1/day2.py` 第 7 题，用 match 实现游戏指令分发

- 按题目给出的按键表实现移动/跳跃/攻击/退出的指令映射，使用选择模式（or-pattern）把每个动作的多个按键合并为一个分支，例如
  `case "上" | "w" | "W"`。
- 外层包 `while True` 循环，`case` 里执行 `break` 才是"退出游戏"；只写单次 `input` 时退出分支没有意义。
- 处理 Esc 键的现实差异：`input()` 是按回车提交的行输入，直接按 Esc 得到的是 `"\x1b"` 字符而不是 `"esc"`，所以退出分支同时匹配
  `"退出"`、`"esc"`/`"ESC"` 和 `"\x1b"`；代码上方注释说明想按一下立即响应需换 curses / msvcrt / readchar。
- 增加 `case _` 兜底，未知指令用 `{action!r}` 打印原始输入，便于排查多余空格等问题。
- 验证：提取 `# 7` 段统一替换 `input()` 后跑 19 个输入（四个方向的中文/小写/大写共 12 个、`跳`、空格、`攻击`、`j`、`J`、未知指令
  `xyz`、`"\x1b"`），输出与预期逐条一致，`\x1b` 触发 break 正常结束；`py_compile` 通过。

## 2026-11-15 16:44

### 修复：`page/homework/section1/day2.py` 季度判断的 match 语法错误

- 现象：`py_compile` 报 `IndentationError: expected an indented block after 'case' statement (line 28)`。原写法把
  `case 3:`、`case 4:`、`case 5:` 堆叠成空分支，而 Python 要求每个 `case` 后必须有缩进块，空 case 并非 fall-through（Python 的
  `match` 不继承 C 的贯穿语义）。
- 修复：合并为选择模式（or-pattern）`case 3 | 4 | 5:`，四个季度分支各写成一行；`case 12 :` 的多余空格一并去掉。
- 验证：`py_compile` 通过；把 `input()` 换成固定值后覆盖 0/1/3/5/6/9/12/13 八种输入，输出依次为 异常/冬/春/春/夏/秋/冬/异常，符合预期。

## 2026-11-15 15:15

### 重构：`page/test1.py` 多级排序的 lambda 拆为独立函数

- `sorted(students, key=lambda x: (x['grade'], x['name']))` 中的匿名函数抽成模块级函数
  `student_sort_key(student: dict) -> tuple[int, str]`，排序调用改为 `key=student_sort_key`。
- 好处：函数有名字和类型注解，堆栈和类型检查器都能直接定位；排序键逻辑与调用点分离，后续复用或改规则只改一处。
- 验证：`.venv/bin/python -m page.test1` 退出码 0，排序结果 `Alice(85), Charlie(85), Bob(92)`，与改动前一致。

## 2026-11-15 11:46

### 修复：`page/test1.py` 的计算器 match 分支

- 取消 `result = ""` 的预声明：初始空串从未被读取，每个分支都会覆盖它，判空时还会打印空行；改为在 `case _` 里也赋值，由
  `case _` 保证所有路径都有值，`print(result)` 保持不变。
- 运算符变量 `c` 改名为 `op`，并由 `int(input())` 改为 `input().strip()`：原写法把运算符转成整数，永远匹配不上 `"+"`
  等字符串，只能落到 `_` 分支。
- 修正 `case "+"` 里误写成 `a * b` 的加法。
- 输出格式去掉 `f"a {c} b = ..."` 里的字面量 `a`/`b`，改为拼接实际数值，如 `7 + 3 = 10`。
- 新增 `case "/" if b == 0` 守卫，避免除零抛 `ZeroDivisionError`。
- 验证：`+`、`/`、`/` 且除数为 0、非法运算符四种输入均输出正确；`ruff check` 未新增告警。

## 2026-11-15 11:12

### 新增：`page/lambda_typing.py`，演示 lambda 参数的类型推断写法

- 背景：lambda 语法不支持参数/返回值注解，本文件演示 5 种让类型检查器认识参数类型的写法：赋值时标注 `Callable`
  、函数参数提供上下文、内置高阶函数（`sort`/`map`）上下文、`cast` 强制标注、改用 `def`。
- 附演示 `functools.partial` 保留原函数注解，以及运行时事实：lambda 的 `__annotations__` 恒为空字典，`cast` 不写入注解。
- 修复演示代码中的一处类型问题：`int ** int` 被推断为 `Any`，`power` 改为 `int(base ** exp)` 以通过 `mypy --strict`。
- 验证：`.venv/bin/python page/lambda_typing.py` 退出码 0；`uvx mypy --strict` 0 报错；另写反例确认检查器能抓到
  `f("hello")` 参数类型不符、`lambda s: s + 1` 在 `sort` 上下文中的 `str + int` 错误，以及无上下文 lambda 参数退化为
  `Any`。

## 2026-11-14 21:27

### 重构：`page/enum_test.py` 改为导入 `enums/weekday_enum.py`，并修复全部告警

- 枚举定义不再重复写：删除文件内的 `WeekdayEnum`，改为 `from enums.weekday_enum import WeekdayEnum`，本文件只保留演示代码。
- 补全原来悬空的 `for item in WeekdayEnum:` 循环体（`IndentationError` 来源），遍历时打印值、成员名、中文名。
- 消除 PyCharm 告警：`_member_map_` 内部字典访问加 `# noinspection PyProtectedMember` 并用 `cast` 还原类型；`find(6)`
  改为先取变量再判空，避免 `None` 成员取属性告警。
- 演示按模块枚举的现有能力改写：成员名用 `MON`/`FRI`/`SUN`，中文名用「星期X」；删掉依赖 `IntEnum` 的与 int 比较、排序及
  `_missing_` 中文名兜底示例。
- 增加项目根目录 `sys.path` 引导，`python page/enum_test.py` 可直接运行。
- 验证：`python page/enum_test.py` 输出正常（退出码 0）；PyCharm 对 `page/enum_test.py`、`enums/weekday_enum.py` 均为 0 告警。
- 备注：编辑过程中 IDE 缓冲区曾把磁盘改动覆盖回去，导致类定义被删；已按完整内容恢复，后续改动建议先确认编辑器里该文件已无未保存修改。

## 2026-11-14 11:34

### 修复：`page/test1.py` 中 `DLog as print` 调用报错

- 现象：`from util.dlog import DLog as print` 后，`print(...)` 抛 `TypeError: DLog() takes no arguments`；文件末尾
  `DLog.d(...)` 抛 `NameError`（别名后 `DLog` 名字不存在）。
- 修复 `util/dlog.py`：为 `DLog` 增加 `__init__(*args, sep=" ", end="\n")`，实例可像内置 `print` 一样多参数调用，输出仍走
  DEBUG 格式并带调用位置；`_print_log` 增加 `end` 透传。
- 修复 `page/test1.py`：`DLog.d(f"list: {l}")` 改为 `print.d(...)`，与新别名保持一致。
- 验证：`PYTHONPATH=. .venv/bin/python -m page.test1` 全量输出正常，`-O` 模式下静默退出码 0；`page/comprehensions_demo.py`
  回归正常。

## 2026-11-14 11:16

### 性能修复：`page/test1.py` 右键运行慢（约 5s）

- 根因：PyCharm 每次运行都会把 `helpers/pycharm_plotly_backend` 等 4 个目录注入 `PYTHONPATH`，其中 `sitecustomize.py` 会
  `import datalore.display`，连带导入 pandas/altair，解释器启动阶段耗时 2~5s。与脚本代码、`uv`、`.venv` 无关（`uv run` 包装仅约
  0.1s）。
    - 实测：原样复制 IDE 的 `PYTHONPATH` 在终端运行 5.04s；去掉 4 个 helper 目录 0.05s。
    - `-X importtime` 显示 `sitecustomize` 2.12s，其中 `pandas` 1.80s（`datalore.display` 引入）。
- 修复：项目根目录新增 `sitecustomize.py`（空文件，仅注释）。项目根位于 `PYTHONPATH` 最前，Python 优先导入它，覆盖 PyCharm
  的绘图后端 sitecustomize。
- 效果：同一 IDE 运行路径由 4~5s 降至 **0.14s**（`idea.log` 收到请求 11:16:09.255 → 脚本首行 11:16:09.399）。
- 代价：PyCharm Plots 工具窗口不再渲染 plotly/matplotlib 图表；需要看图时删除 `sitecustomize.py` 即可恢复。
- 文档：`README.md` 增加 PyCharm 右键运行说明，解释 `sitecustomize.py` 的作用与删除影响。

## 2026-11-14 10:51

### 性能排查：`page/test1.py` 运行耗时约 6s

- 结论：耗时与 Python 代码、`uv`、`.venv` 无关，全部来自 IDE 与系统资源争抢。
    - 实测：`.venv/bin/python page/test1.py` 0.05s；`uv run`（cwd=page）0.09s；`uv` 自身启动 0.016s。
- 根因：一个失控的 Dart 语言服务器 `PID 11317 dart language-server --protocol lsp`，98% CPU 空转近 2 小时、占用 3.75GB。
    - 来源：08:54 在 `~`（家目录）启动的 Claude Code 会话（PID 11268）拉起的 dart MCP server，把整个家目录当作工作区索引。
    - 叠加因素：系统 load 5–7、PyCharm 堆上限仅 `-Xmx2048m` 而 RSS 达 3.75GB、GitHub Copilot 插件 32 次网络失败重试。
- 处理：结束 `11286`（dart mcp-server）与 `11317`（language-server）两个进程。
- 效果：PyCharm 内部单次 Run 处理耗时由 **6.26s → 0.005s**（取自 `idea.log` 时间戳），系统 load 由 5.0 降至 3.8。

### 遗留建议

- 重启 PyCharm：清除进程内残留的旧 `VIRTUAL_ENV`（当前每次运行仍打印 uv 警告，耗时约 0.04s）。
- 建议将 PyCharm `-Xmx2048m` 提升至 4096m；不使用 Copilot 可禁用该插件。
- 后续在项目目录启动 Claude Code，避免 dart MCP server 以家目录为 root 索引。

## 2026-11-14 10:38

### 环境修复

- 根治 uv 警告 `VIRTUAL_ENV ... does not match the project environment path`：与 10:31 那次不同，本次问题不在 `.venv`
  内部，而在 shell 会话继承的 **脏环境变量**。
    - 原因：启动 Claude Code 的终端曾在旧目录 `~/GitHub/python_projects/python_templet_project` 执行过 `activate`
      ，项目迁移后该目录已不存在，但 `VIRTUAL_ENV` 与 `PATH` 首项仍指向它。`.venv` 本身健康（shebang、`activate`、`pyvenv.cfg`
      全部正确，旧路径残留为 0）。
    - 副作用：`PATH` 首位是无效目录，导致裸 `python` 落到系统 `/usr/local/bin/python3` 而非项目 venv。
- `~/.zshrc` 末尾新增 `[venv-guard]` 段：`VIRTUAL_ENV` 指向不存在的目录时自动 `unset`，并从 `PATH` 剔除已失效的
  `*/.venv/bin` 条目；正常 `activate` 不受影响。修改前已备份至 `~/.zshrc.bak.20261114-103841`。

### 验证

- 脏值场景：新 shell 中 `VIRTUAL_ENV` 为空、旧 `PATH` 条目为 0，`uv run python` 无警告且指向
  `~/GitHub/python_templet_project/.venv/bin/python`。
- 合法场景：`VIRTUAL_ENV` 指向存在的 `.venv` 时被保留，未被误清理。

## 2026-11-14 10:31

### 环境修复

- 重建 `.venv`，消除 uv 警告：`VIRTUAL_ENV ... does not match the project environment path`。
    - 原因：venv 创建于旧目录 `~/GitHub/python_projects/python_templet_project/.venv`，项目迁移后 `activate` 及 18
      个脚本仍写死旧路径，旧目录已不存在。
    - 操作：`mv .venv .venv.old` → `uv sync` → 验证后 `rm -rf .venv.old`。
    - `pyproject.toml` / `uv.lock` 未改动，118 个包与重建前完全一致。

### 验证

- 新 `.venv/bin` 中旧路径残留为 0，`activate` 中 `VIRTUAL_ENV` 指向 `~/GitHub/python_templet_project/.venv`。
- `uv sync --check` 输出 `Would make no changes`。
- `streamlit` / `pydantic_ai` / `anthropic` / `openai` / `fastapi` 导入正常。

## 2026-11-08 16:01

### 安全修复

- 使用 `git filter-repo` 重写全部历史，从所有提交中彻底移除 `.env`。
    - 命令：`git filter-repo --path .env --invert-paths --force`
    - 重写后所有提交哈希发生变化，`main` / `develop` 已同步至新历史。
    - 重写前已备份至 `/Users/shang/GitHub/python_templet_project-backup-20261108.bundle`。
- filter-repo 清理了未跟踪文件，已从备份 bundle 恢复本地 `.env`（仅存在于工作区，不再被追踪）。

### 验证

- `git log --all -- .env` 输出为空；`git rev-list --all --objects | grep .env` 无结果。
- 本地 `.env` 文件保留（648 字节），忽略规则仍生效。

## 2026-11-08 15:56

### 安全修复

- `.gitignore`：新增环境变量文件忽略规则（`.env`、`.env.*`）。
- 执行 `git rm --cached .env` 停止跟踪 `.env`，本地文件保留。

### 说明

- `.env` 内含 `ANTHROPIC_AUTH_TOKEN` 等敏感凭据，推送到公开仓库会导致泄露。
- 后续处理：轮换已暴露的 Token；如需彻底清除历史，可使用 `git filter-repo` 重写历史。

## 2026-11-04 08:58

### 调整

- `model/student_model.py`、`model/book_model.py`、`model/book_library_model.py`：由 `@dataclass` 迁移为 Pydantic
  `BaseModel`。
    - `Student`：`library_password` 使用 `Field(repr=False)` 隐藏；`member_level` 按枚举值自动校验（`"normal"` /
      `"vip"`）。
    - `StudentModel.to_dict()` 改为 `model_dump(mode="json")`，枚举自动序列化为原始值。
    - `BookModel.from_dict()` 改为 `model_validate()`，JSON 中多余的 `industry` 字段自动忽略。
    - `BookLibraryModel`：`books` 改为带默认工厂的 Pydantic 字段，原有方法保持不变。
- `page/student.py`：解码改用 `StudentModel.model_validate()`。
- `page/book_managment_system/book_managment_system.py`：修正 `book_out()` 中不存在的字段 `isLetOut`，改为 `is_borrow`
  （Pydantic 不允许给未声明字段赋值）。
- `pyproject.toml`：新增直接依赖 `pydantic>=2.13.0`（原为 pydantic-ai 的间接依赖）。

### 验证

- `python page/student.py` 正常输出成绩统计。
- 图书加载 100 本、按 ISBN 查询、借书状态变更均正常。
- 学生模型枚举解码、`to_dict()` 序列化、repr 隐藏密码、`==` / `<` 比较均验证通过。
- `ruff check model/` 无告警。

## 2026-11-03 21:12

### 新增

- `assets/json/books.json`：新增 100 本大学图书数据，覆盖信息技术、机械制造、电子信息、土木建筑、医学健康、经济管理、法学、教育学、文学人文、环境能源
  10 个主流行业，每个行业 10 本；ISBN 为带合法校验位的示例数据。
- `model/book_library_model.py`：新增 `BOOKS_JSON_PATH` 默认数据路径和 `load_books()` 方法，解析 JSON 后载入 `books` 并返回
  `list[BookModel]`。

### 验证

- `load_books()` 解析出 100 本图书，首尾记录正确；`find_book_by_isbn()` 可按 ISBN 命中；`ruff check` 无告警。

## 2026-11-03 21:05

### 调整

- `model/book_model.py`：`BookModel` 改为 `@dataclass` 实现，保留 `title`、`author`、`isbn` 字段。
    - 新增 `from_dict` / `to_dict`，支持字典与模型互转。
    - 新增 `__str__`；`__eq__` / `__lt__` 以 ISBN 作为唯一标识，便于比较和排序。

### 验证

- 构造、编解码往返、同 ISBN 相等性、排序均验证通过；`ruff check` 无告警。

## 2026-11-03 20:48

### 新增

- `enums/member_level_enum.py`：新增 `MemberLevelEnum` 会员等级枚举，包含 `NORMAL`（普通）、`VIP`。
- `model/student_model.py`：`Student` 新增属性：
    - `member_level`：图书馆会员等级，默认 `MemberLevelEnum.NORMAL`。
    - `borrowed_books`：已借图书列表，默认空列表。
    - `library_password`：图书馆密码，默认空字符串，并在 `repr` 中隐藏。

### 调整

- `StudentModel.from_dict`：支持新字段解码，旧成绩 JSON 缺少字段时使用默认值。
- `StudentModel.to_dict`：会员等级输出为原始值（`normal` / `vip`），便于 JSON 序列化。

### 验证

- `python3 page/student.py` 正常运行。
- 新字段编码/解码往返验证通过；`ruff check` 无告警。

## 2026-11-03 20:43

### 删除

- `model/student.py`：移除旧的 `Student` / `CodableModel` 模型文件。

### 调整

- `enum/` 目录重命名为 `enums/`：避免与 Python 标准库 `enum` 同名，否则 `from enum.weekday_enum import WeekdayEnum` 会报
  `ModuleNotFoundError: No module named 'enum.weekday_enum'; 'enum' is not a package`。
- `page/codable.py`：`CodableModel`、`Student` 类迁移到本文件内，枚举改用 `enums/weekday_enum.py` 中的 `WeekdayEnum`。
- 已验证：`python3 page/codable.py` 编码/解码输出正常（`weekday: 1` ↔ `星期一`）。

## 2026-11-02 16:31

### 修复

- `docs/PyCharm-Streamlit外部工具配置.md`：修正 External Tool 配置——工作目录改为项目根目录 `$ProjectFileDir$`，并增加环境变量
  `PYTHONPATH=$ProjectFileDir$`，解决 `ModuleNotFoundError: No module named 'base_widget'`。
- 已实测：从项目根目录带 `PYTHONPATH=.` 启动 `page/streamlit_demo.py`，健康检查返回 200。

## 2026-11-02 16:29

### 修复

- `docs/PyCharm-Streamlit外部工具配置.md`：补充“工作目录末尾多空格导致无法启动进程”的排错说明。

## 2026-11-02 16:23

### 文档

- 新增 `docs/PyCharm-Streamlit外部工具配置.md`：PyCharm 右键通过 `uv` 启动 Streamlit 的 External Tools 配置说明与排错指南。
- 无代码改动；由用户在 PyCharm 中按文档手动配置。

## 2026-11-02 12:52

### 调整

- `page/ai_robot/app.py`：取消聊天输入框聚焦时的高亮效果。
    - 移除 `stChatInput:focus-within` 的蓝色边框与外发光。
    - 将输入框内层容器的聚焦红色边框置为透明，聚焦前后样式保持一致。

## 2026-11-02 12:44

### 修复

- `page/ai_robot/app.py`：修复底部“深度思考 / 智能搜索”胶囊与输入框重叠。
    - 抵消 Streamlit Markdown 容器默认的 `margin-bottom: -1rem` 和固定高度，让胶囊区域按实际高度占位。
    - 底部工具区与输入框间距调整为 0.5rem；实测桌面端和移动端胶囊底部与输入框顶部间隔 14px。
- `page/ai_robot/app.py`：修复侧栏底部用户昵称与“免费版”显示不全。
    - 头像、昵称、套餐改为单行 Flex 布局，头像固定 34px，昵称超长时单行省略。
    - 解除用户信息区 Markdown 的负外边距与固定高度，底部信息不再被侧栏 `overflow: hidden` 裁剪。
    - 移动端历史区限高由 22vh 调整为 18vh，避免页面自动下移遮挡侧栏顶部 Logo。

## 2026-11-02 11:48

### 界面重构

- `page/ai_robot/app.py`：重构为 DeepSeek 网页版暗色风格，保留 SQLite 历史、流式回答、图片/文档上传等真实功能。
    - 使用 `st.columns([1, 3.5])` 分栏，左侧用自定义 `st.container` 模拟侧栏，不使用原生 `st.sidebar`。
    - 侧栏包含 Logo、搜索、全宽圆角“新建对话”、按置顶/今天/昨天/更早分组的历史记录、当前会话高亮与操作菜单、底部用户信息。
    - 主区包含吸顶会话标题、分享图标、用户右侧气泡、助手消息操作图标。
    - 围栏代码块拆分为带语言标签与复制按钮的深色代码块，并补充行内代码、加粗、列表、标题等 Markdown 样式。
    - 底部输入区固定在页面下方，包含“深度思考”“智能搜索”胶囊、附件按钮与蓝色发送按钮；底部容器不再拦截侧栏点击。
    - 增加移动端适配：窄屏下侧栏改为文档流布局、历史区限高滚动、分栏保持横排。
- `page/ai_robot/chat_store.py`：新增 `pinned` 字段与自动迁移，支持会话置顶/取消置顶。

### 修复

- 修复侧栏分组标题与历史按钮重叠。
- 修复用户消息气泡未右对齐。
- 修复代码块语言栏与代码区重叠、复制按钮不可见及按钮底色过亮。
- 修复顶栏滚动后消失。
- 移除历史条目的悬浮提示，避免遮挡分组标题。

## 2026-11-02 11:08

### 新增

- `page/ai_robot/app.py`：等待后端时显示动态状态图标。
    - 等待阶段：紧凑状态框 + `:shimmer[正在等待后端响应…]` 动画文字，状态图标旋转。
    - 收到首块内容后：切换为 `:shimmer[正在生成回答…]`。
    - 完成后显示“回答完成”勾选图标；失败时显示“请求失败”错误图标。
    - 状态框内展示当前使用的模型名称。
- `page/ai_robot/llm_client.py`：新增 `pick_model()`，供界面显示实际选用的模型。

## 2026-11-02 10:57

### 文档

- `README.md`：补充 AI 机器人启动命令（含端口占用时的备用命令）。

## 2026-11-02 10:53

### 新增

- `page/ai_robot/`：Streamlit AI 聊天机器人。
    - `app.py`：聊天界面，流式输出；左侧会话历史列表，支持新建、切换、删除。
    - `chat_store.py`：SQLite 持久化会话与消息，上传文件保存到 `data/uploads/<会话ID>/`。
    - `file_reader.py`：PDF / Word / Excel / PPT / 文本文字提取，图片类型识别。
    - `llm_client.py`：Anthropic 兼容接口，含图片时自动切换 `ANTHROPIC_VISION_MODEL`。
- 输入框支持多文件上传：图片（png/jpg/jpeg/webp/gif）原生发送，文档提取文字后拼入上下文。
- 会话自动命名（取首条消息前 20 字，无文字时取首个文件名）。

### 依赖

- `pyproject.toml` / `uv.lock`：新增 `pypdf`、`python-docx`、`openpyxl`、`python-pptx`。

### 其他

- `.gitignore`：忽略 `page/ai_robot/data/` 运行时数据。

## 2026-11-02 10:36

### 修复

- `page/ai_client.py`：由 OpenAI SDK 改为 Anthropic SDK，按 `.env` 中的 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` /
  `ANTHROPIC_MODEL` 调用模型。
- 问答改为流式输出（`client.messages.stream` + `text_stream`），逐字打印。
- 增加鉴权失败、模型不存在、限流、网络异常等中文错误提示，出错后不退出程序。
- 支持 Ctrl+C / EOF 优雅退出。

### 依赖

- `pyproject.toml` / `uv.lock`：新增 `anthropic>=0.95.0`。
