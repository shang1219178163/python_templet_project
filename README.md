# python_templet_project

用 uv 管理的个人 python 项目工程

运行本地文件 main.py 命令：

```bash
.venv/bin/python main.py
```

PyCharm 右键运行说明：

项目根目录的 `sitecustomize.py` 用于抵消 PyCharm 每次运行注入的绘图后端开销（其 `sitecustomize` 会连带导入
pandas，使解释器启动多花 2~5 秒）。该文件对普通 Python 进程不做任何事。若删除它，PyCharm 的 Plots 工具窗口会恢复接管
plotly/matplotlib 渲染，但右键运行会重新变慢。

运行 Streamlit 演示页：

```bash
PYTHONPATH=. .venv/bin/streamlit run app/page/streamlit_demo.py
```

运行 AI 机器人聊天页：

```bash
PYTHONPATH=. .venv/bin/streamlit run app/page/ai_robot/chat.py
```

若 8501 端口已被占用，可指定其他端口：

```bash
PYTHONPATH=. .venv/bin/streamlit run app/page/ai_robot/chat.py --server.port 8502
```

默认打开 http://localhost:8501 ；指定端口时改为对应端口。

启动 FastAPI 图书查询服务（首次启动会自动建表并写入示例图书）：

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

接口文档 http://127.0.0.1:8001/docs ；接口：`GET /`（欢迎信息）、`GET /books`（图书列表）、
`GET /books/count`（图书总数）、`GET /books/{id}`（图书详情）、`POST /books`（新增）、
`PATCH /books/{id}`（局部更新）、`DELETE /books/{id}`（删除）。端口被占用时可改用 `--port` 指定其他端口。

`GET /books` 默认走游标分页；显式传 `page` 时走普通分页：

```bash
# 游标分页（默认）：首次不传 cursor 或传空都可以
curl "http://127.0.0.1:8001/books?page_size=20"
curl "http://127.0.0.1:8001/books?cursor=&page_size=20"

# 普通分页：返回 total / page
curl "http://127.0.0.1:8001/books?page=1&page_size=20"
```

`page_size` 默认 20、上限 100；`page` 与有值的 `cursor` 同时传会返回 422。

`GET /books` 还支持模糊搜索与排除指定 id（默认同样走游标分页，需要 `total` 时加 `page=1`）：

```bash
# 在书名 / 作者 / ISBN 中模糊搜索
curl "http://127.0.0.1:8001/books?keyword=算法&page=1"

# 排除 id=1、2 的数据（逗号分隔或重复参数均可）
curl "http://127.0.0.1:8001/books?exclude=1,2&page=1"
curl "http://127.0.0.1:8001/books?exclude=1&exclude=2&page=1"
```

数据存放在 `data/app.db`（SQLite，与代码包分离）。种子数据源为 `app/assets/json/book.json`
（100 条，含 `title` / `author` / `publisher` / `isbn` / `price` / `total_num` / `stock`）。
`price` 为各书常见版次的官方定价，版次或印次不同时价格会有差异。也可手动初始化：

```bash
PYTHONPATH=. .venv/bin/python -m app.db.init
```

默认使用 SQLite；要切到 MySQL，在 `.env` 或环境变量里配置 `DATABASE_URL`：

```dotenv
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/bookdb?charset=utf8mb4
```

驱动 `pymysql` 已在项目依赖中，服务端需先建库：`CREATE DATABASE bookdb DEFAULT CHARSET utf8mb4;`。
切换细节与兼容性说明见 `docs/SQLite与MySQL切换.md`。

用的是 SQLAlchemy ORM 与 pydantic 分层模型，说明见 `docs/ORM进模型出模型最佳实践.md`。
`app/main.py` 负责创建应用、注册路由与异常处理，接口路由在 `app/api/routes/`，数据库代码在 `app/db/`。
成功与失败响应统一为 `ApiResponse` 结构（`code` / `message` / `data`）。

也可用 FastAPI CLI 启动（依赖 `fastapi[standard]`，本项目已安装）。注意必须带 `PYTHONPATH=.`，否则脚本 `sys.path` 里没有项目根目录，会报
`No module named 'lib'`：

```bash
PYTHONPATH=. .venv/bin/fastapi dev app/main.py --port 8001
```

`fastapi deploy` 是把应用部署到 FastAPI Cloud 的命令，本地开发用上面的 `dev` 或 `uvicorn`。

停止 FastAPI 服务：前台运行时按 `Ctrl+C`；后台运行时按端口结束进程：

```bash
lsof -ti :8001 | xargs kill
```

AI 机器人使用 DeepSeek 风格暗色界面，支持流式回答、SQLite 会话历史、会话置顶/删除，以及图片和 PDF/Word/Excel/PPT/文本上传。

依赖：`streamlit`、`anthropic`、`python-dotenv`、`pypdf`、`python-docx`、`openpyxl`、`python-pptx`（Pillow 随 Streamlit 安装）。

`.env` 中需配置：

```dotenv
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=你的密钥
ANTHROPIC_MODEL=deepseek-flash
ANTHROPIC_VISION_MODEL=deepseek-flash
```

配置加载集中在 `app/config.py`（`pydantic-settings`），其他模块统一 `from app.config import settings`，
不要再各自调用 `load_dotenv()`。优先级：已存在的环境变量 > `.env` > 代码里的默认值。