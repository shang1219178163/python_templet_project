# CHANGELOG

## 2026-11-14 11:16

### 性能修复：`page/test1.py` 右键运行慢（约 5s）

- 根因：PyCharm 每次运行都会把 `helpers/pycharm_plotly_backend` 等 4 个目录注入 `PYTHONPATH`，其中 `sitecustomize.py` 会 `import datalore.display`，连带导入 pandas/altair，解释器启动阶段耗时 2~5s。与脚本代码、`uv`、`.venv` 无关（`uv run` 包装仅约 0.1s）。
  - 实测：原样复制 IDE 的 `PYTHONPATH` 在终端运行 5.04s；去掉 4 个 helper 目录 0.05s。
  - `-X importtime` 显示 `sitecustomize` 2.12s，其中 `pandas` 1.80s（`datalore.display` 引入）。
- 修复：项目根目录新增 `sitecustomize.py`（空文件，仅注释）。项目根位于 `PYTHONPATH` 最前，Python 优先导入它，覆盖 PyCharm 的绘图后端 sitecustomize。
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
- 根治 uv 警告 `VIRTUAL_ENV ... does not match the project environment path`：与 10:31 那次不同，本次问题不在 `.venv` 内部，而在 shell 会话继承的**脏环境变量**。
  - 原因：启动 Claude Code 的终端曾在旧目录 `~/GitHub/python_projects/python_templet_project` 执行过 `activate`，项目迁移后该目录已不存在，但 `VIRTUAL_ENV` 与 `PATH` 首项仍指向它。`.venv` 本身健康（shebang、`activate`、`pyvenv.cfg` 全部正确，旧路径残留为 0）。
  - 副作用：`PATH` 首位是无效目录，导致裸 `python` 落到系统 `/usr/local/bin/python3` 而非项目 venv。
- `~/.zshrc` 末尾新增 `[venv-guard]` 段：`VIRTUAL_ENV` 指向不存在的目录时自动 `unset`，并从 `PATH` 剔除已失效的 `*/.venv/bin` 条目；正常 `activate` 不受影响。修改前已备份至 `~/.zshrc.bak.20261114-103841`。

### 验证
- 脏值场景：新 shell 中 `VIRTUAL_ENV` 为空、旧 `PATH` 条目为 0，`uv run python` 无警告且指向 `~/GitHub/python_templet_project/.venv/bin/python`。
- 合法场景：`VIRTUAL_ENV` 指向存在的 `.venv` 时被保留，未被误清理。

## 2026-11-14 10:31

### 环境修复
- 重建 `.venv`，消除 uv 警告：`VIRTUAL_ENV ... does not match the project environment path`。
  - 原因：venv 创建于旧目录 `~/GitHub/python_projects/python_templet_project/.venv`，项目迁移后 `activate` 及 18 个脚本仍写死旧路径，旧目录已不存在。
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
- `model/student_model.py`、`model/book_model.py`、`model/book_library_model.py`：由 `@dataclass` 迁移为 Pydantic `BaseModel`。
  - `StudentModel`：`library_password` 使用 `Field(repr=False)` 隐藏；`member_level` 按枚举值自动校验（`"normal"` / `"vip"`）。
  - `StudentModel.to_dict()` 改为 `model_dump(mode="json")`，枚举自动序列化为原始值。
  - `BookModel.from_dict()` 改为 `model_validate()`，JSON 中多余的 `industry` 字段自动忽略。
  - `BookLibraryModel`：`books` 改为带默认工厂的 Pydantic 字段，原有方法保持不变。
- `page/student.py`：解码改用 `StudentModel.model_validate()`。
- `page/book_managment_system/book_managment_system.py`：修正 `book_out()` 中不存在的字段 `isLetOut`，改为 `is_borrow`（Pydantic 不允许给未声明字段赋值）。
- `pyproject.toml`：新增直接依赖 `pydantic>=2.13.0`（原为 pydantic-ai 的间接依赖）。

### 验证
- `python page/student.py` 正常输出成绩统计。
- 图书加载 100 本、按 ISBN 查询、借书状态变更均正常。
- 学生模型枚举解码、`to_dict()` 序列化、repr 隐藏密码、`==` / `<` 比较均验证通过。
- `ruff check model/` 无告警。

## 2026-11-03 21:12

### 新增
- `assets/json/books.json`：新增 100 本大学图书数据，覆盖信息技术、机械制造、电子信息、土木建筑、医学健康、经济管理、法学、教育学、文学人文、环境能源 10 个主流行业，每个行业 10 本；ISBN 为带合法校验位的示例数据。
- `model/book_library_model.py`：新增 `BOOKS_JSON_PATH` 默认数据路径和 `load_books()` 方法，解析 JSON 后载入 `books` 并返回 `list[BookModel]`。

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
- `model/student_model.py`：`StudentModel` 新增属性：
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
- `enum/` 目录重命名为 `enums/`：避免与 Python 标准库 `enum` 同名，否则 `from enum.weekday_enum import WeekdayEnum` 会报 `ModuleNotFoundError: No module named 'enum.weekday_enum'; 'enum' is not a package`。
- `page/codable.py`：`CodableModel`、`Student` 类迁移到本文件内，枚举改用 `enums/weekday_enum.py` 中的 `WeekdayEnum`。
- 已验证：`python3 page/codable.py` 编码/解码输出正常（`weekday: 1` ↔ `星期一`）。

## 2026-11-02 16:31

### 修复
- `docs/pycharm-streamlit-external-tool.md`：修正 External Tool 配置——工作目录改为项目根目录 `$ProjectFileDir$`，并增加环境变量 `PYTHONPATH=$ProjectFileDir$`，解决 `ModuleNotFoundError: No module named 'base_widget'`。
- 已实测：从项目根目录带 `PYTHONPATH=.` 启动 `page/streamlit_demo.py`，健康检查返回 200。

## 2026-11-02 16:29

### 修复
- `docs/pycharm-streamlit-external-tool.md`：补充“工作目录末尾多空格导致无法启动进程”的排错说明。

## 2026-11-02 16:23

### 文档
- 新增 `docs/pycharm-streamlit-external-tool.md`：PyCharm 右键通过 `uv` 启动 Streamlit 的 External Tools 配置说明与排错指南。
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
- `page/ai_client.py`：由 OpenAI SDK 改为 Anthropic SDK，按 `.env` 中的 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL` 调用模型。
- 问答改为流式输出（`client.messages.stream` + `text_stream`），逐字打印。
- 增加鉴权失败、模型不存在、限流、网络异常等中文错误提示，出错后不退出程序。
- 支持 Ctrl+C / EOF 优雅退出。

### 依赖
- `pyproject.toml` / `uv.lock`：新增 `anthropic>=0.95.0`。
