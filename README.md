# python_templet_project
用 uv 管理的个人 python 项目工程

运行本地文件 main.py 命令：

```bash
.venv/bin/python main.py
```

运行 Streamlit 演示页：

```bash
PYTHONPATH=. .venv/bin/streamlit run page/streamlit_demo.py
```

运行 AI 机器人聊天页：

```bash
PYTHONPATH=. .venv/bin/streamlit run page/ai_robot/app.py
```

若 8501 端口已被占用，可指定其他端口：

```bash
PYTHONPATH=. .venv/bin/streamlit run page/ai_robot/app.py --server.port 8502
```

默认打开 http://localhost:8501 ；指定端口时改为对应端口。

AI 机器人使用 DeepSeek 风格暗色界面，支持流式回答、SQLite 会话历史、会话置顶/删除，以及图片和 PDF/Word/Excel/PPT/文本上传。

依赖：`streamlit`、`anthropic`、`python-dotenv`、`pypdf`、`python-docx`、`openpyxl`、`python-pptx`（Pillow 随 Streamlit 安装）。

`.env` 中需配置：

```dotenv
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=你的密钥
ANTHROPIC_MODEL=deepseek-flash
ANTHROPIC_VISION_MODEL=deepseek-flash
```