# python_templet_project
用 uv 管理的个人 python 项目工程

运行本地文件 main.py 命令：

```bash
.venv/bin/python main.py
```

PyCharm 右键运行说明：

项目根目录的 `sitecustomize.py` 用于抵消 PyCharm 每次运行注入的绘图后端开销（其 `sitecustomize` 会连带导入 pandas，使解释器启动多花 2~5 秒）。该文件对普通 Python 进程不做任何事。若删除它，PyCharm 的 Plots 工具窗口会恢复接管 plotly/matplotlib 渲染，但右键运行会重新变慢。

运行 Streamlit 演示页：

```bash
PYTHONPATH=. .venv/bin/streamlit run lib/page/streamlit_demo.py
```

运行 AI 机器人聊天页：

```bash
PYTHONPATH=. .venv/bin/streamlit run lib/page/ai_robot/app.py
```

若 8501 端口已被占用，可指定其他端口：

```bash
PYTHONPATH=. .venv/bin/streamlit run lib/page/ai_robot/app.py --server.port 8502
```

默认打开 http://localhost:8501 ；指定端口时改为对应端口。

启动 FastAPI 图书查询服务：

```bash
PYTHONPATH=. .venv/bin/uvicorn lib.api.book:app --host 127.0.0.1 --port 8001 --reload
```

接口文档 http://127.0.0.1:8001/docs ；接口：`GET /`（欢迎信息）、`GET /books`（图书列表）、`GET /books/count`（图书总数）。端口被占用时可改用 `--port` 指定其他端口。

也可用 FastAPI CLI 启动（依赖 `fastapi[standard]`，本项目已安装）。注意必须带 `PYTHONPATH=.`，否则脚本 `sys.path` 里没有项目根目录，会报 `No module named 'lib'`：

```bash
PYTHONPATH=. .venv/bin/fastapi dev lib/api/book.py --port 8001
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