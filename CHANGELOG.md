# CHANGELOG

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
