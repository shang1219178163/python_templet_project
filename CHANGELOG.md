# CHANGELOG

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
