# CHANGELOG

## 2026-11-16 16:13

### 修复：`filter_data` 把 `**kwargs` 注解成 `dict[str, Any]` 导致的类型警告

- 警告现象：四个配置项赋值处报「应为类型 int/bool/str，但实际为 `dict[str, Any] | int`」，两个调用处每个关键字实参都报「应为 `dict[str, Any]`」。
- 根因：`**kwargs: X` 注解的是**每个关键字参数的值类型**，不是整个 kwargs 的类型。写成 `dict[str, Any]` 等于声明「每个值都是字典」。
- 修复：签名改为 `**kwargs: Any`（值类型为 Any），局部注解保持不变；调用处与 `.get()` 处警告全部消失。
- 验证：`ruff check` 通过；PyCharm 仅剩 `goods_total_amount` 原有的 `price_sum_new` 弱警告；两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 16:07

### 修复：`filter_data` 四个配置项赋值处的类型不匹配警告

- 保留「带默认值的局部注解」写法：`threshold: int = kwargs.get("threshold", 1)` 等四行不变。
- 把签名中的 `**kwargs: int | str | bool` 改为 `**kwargs: Any`：原联合类型里每个键实际类型不同，逐个赋给 `int`/`bool`/`str` 时 PyCharm 报「应为类型 X，但实际为 int | str | bool」共 4 条。
- 清理遗留的 `cast` 未使用导入；`if unique is True` 已简化为 `if unique`。
- 验证：`ruff check` 全部通过；PyCharm 仅剩 `goods_total_amount` 原有的 `price_sum_new` 弱警告；两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:40

### 调整：`filter_data` 的过滤恢复为 `filter` + `lambda` 写法

- 把列表推导式改回 `list(filter(lambda x: x >= limit, items))`，并在分支内用 `limit: int = threshold` 显式收窄：lambda 会捕获 `limit`（已声明为 `int`），不再把 `threshold` 推断成含 `None` 的联合类型。
- 行为与推导式版本完全一致；PyCharm 该行警告消除，`ruff check` 通过。
- 验证：两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:38

### 修复：`page/homework/section1/day5.py` 中 `filter_data` 的 `None` 比较警告

- 警告内容：`'int | str | bool | None' 的成员 'None' 没有特性 '__le__'`。根因是 `**kwargs: int | str | bool` 把所有配置值混成一个联合类型，`kwargs.get("threshold", None)` 再叠加 `None`，PyCharm 无法在 lambda 闭包里把 `threshold` 收窄成数值。
- 新增 `FilterOptions(TypedDict, total=False)` 精确描述四个配置项类型，函数签名改为 `**kwargs: Unpack[FilterOptions]`，`.get("threshold")` 的类型变为 `int | None`。
- 过滤改用列表推导式，并在分支内用 `limit: int = threshold` 显式收窄类型，消除闭包类型推断问题；行为与原 `filter` 写法一致。
- 验证：`ruff check` 全部通过；PyCharm 检查该文件仅剩 `goods_total_amount` 里原有的 `price_sum_new` 未使用弱警告；`filter_data` 两组用例输出 `[9, 8, 7, 5]`、`[1, 3, 5]` 不变。

## 2026-11-16 15:10

### 修复：`page/homework/section1/day5.py` 中 `analyze_scores` 的 IDE 警告

- 删除误导入且未使用的 `from itertools import count`：它导致 `goods_total_amount` 和 `analyze_scores` 里的局部变量 `count` 被判为「隐藏外部作用域名称」（ruff F401/F811，PyCharm weak warning）。
- 三个配置项改用 `kwargs.get(key, 默认值)`：原写法 `pass_line` 取值时误判 `show_detail is not None`，且 `kwargs.get()` 可能返回 `None`，PyCharm 报「`Literal[60] | None | Any` 的成员 `None` 没有 `__le__`」以及 `round()` 实参不匹配。
- 按题目要求补全类型注解：`*args: float`、`**kwargs: Any`、返回 `dict[str, int | float | str]`，并修正空分数分支的缩进。
- 验证：`ruff check` 全部通过；PyCharm 检查 `analyze_scores` 已无警告；脚本运行输出 `report1`、`report2` 与预期数值一致。

## 2026-11-16 11:19

### 调整：`page/date_demo.py` 改为不封装函数，直接演示底层 API

- 按要求去掉全部函数定义，改为顺序脚本：每段先调用 API 再打印结果，读者可以直接看到输入与输出。
- 保留 10 个演示段：字符串→datetime、datetime→字符串、datetime→时间戳、时间戳→datetime（本地/UTC）、字符串→时间戳、时间戳→字符串、往返断言、带 `%z` 的时区字符串、`fromisoformat`、当前时间三形态（秒/毫秒时间戳）。
- 验证：`.venv/bin/python page/date_demo.py` 退出码 0，输出与封装版一致，往返断言通过。

## 2026-11-16 11:13

### 新增：`page/date_demo.py`，字符串 / datetime / 时间戳三种时间形态互转

- 提供 6 个函数：`str_to_datetime`、`datetime_to_str`、`datetime_to_timestamp`、`timestamp_to_datetime`、`str_to_timestamp`、`timestamp_to_str`，覆盖字符串 ⇄ datetime ⇄ 时间戳的全部方向，统一使用 `DEFAULT_FMT = "%Y-%m-%d %H:%M:%S"`。
- 演示带时区场景：`fmt` 加 `%z` 才能保留时区；`fromtimestamp(tz=timezone.utc)` 返回 aware 时间；ISO 字符串可直接用 `datetime.fromisoformat`（3.11+ 支持末尾 `Z`）。
- 注释说明 naive datetime 调用 `timestamp()` 时按本地时区解释，跨时区计算应显式传 `tz`。
- 验证：`.venv/bin/python page/date_demo.py` 退出码 0，字符串往返、timestamp 往返、带时区字符串往返断言全部通过，本地时间输出 `2026-11-16 10:57:00`。

## 2026-11-16 10:57

### 修复：`page/homework/section1/day5.py` 的 `second2date` 秒数换算

- 保持原有「年/月/日 时:分:秒」的换算结构（365 天/年、30 天/月的近似口径），改用 `divmod` 逐级取商和余数。
- 修复三处错误：`/` 真除法导致 年/月/日/时/分 全是浮点数；`v % year` 对浮点数取模得到的是无意义的零头，应使用上一级的余数；`hour = v / 3600` 未扣除整天的秒数。
- 分/秒改为 `:02d` 补零，函数补上 `-> str` 返回类型注解。
- 移除误导入的 `from unittest import result`。
- 验证：时间戳 `1794797837` → `56:11:3 02:57:17`；`3725` → `0:0:0 01:02:05`；`86400` → `0:0:1 00:00:00`，均与预期一致。

## 2026-11-16 10:19

### 新增：`docs/python-del-usage.md`，整理 Python `del` 的使用场景

- 按场景分七节：删除变量绑定、列表元素（索引/切片/清空）、字典键、对象/类属性、导入名、遍历中删除的陷阱、函数内删全局名。
- 补充 `del lst[i]` / `remove` / `pop` / `clear` / `del lst` 的对比表，以及 `del lst[:]` 保留容器对象、`del lst` 只删名字的区别。
- 指出遍历中删除会抛 `RuntimeError`（字典）或漏删（列表），给出 `list(d)` 快照和推导式重建两种正确做法。
- 关联图书管理系统 `day4.py` 的场景：删除图书应写 `del books[book_name]`，不要用 `books[book_name] = None`。

## 2026-11-15 17:26

### 新增：`page/homework/section1/day2.py` 第 7 题，用 match 实现游戏指令分发

- 按题目给出的按键表实现移动/跳跃/攻击/退出的指令映射，使用选择模式（or-pattern）把每个动作的多个按键合并为一个分支，例如 `case "上" | "w" | "W"`。
- 外层包 `while True` 循环，`case` 里执行 `break` 才是"退出游戏"；只写单次 `input` 时退出分支没有意义。
- 处理 Esc 键的现实差异：`input()` 是按回车提交的行输入，直接按 Esc 得到的是 `"\x1b"` 字符而不是 `"esc"`，所以退出分支同时匹配 `"退出"`、`"esc"`/`"ESC"` 和 `"\x1b"`；代码上方注释说明想按一下立即响应需换 curses / msvcrt / readchar。
- 增加 `case _` 兜底，未知指令用 `{action!r}` 打印原始输入，便于排查多余空格等问题。
- 验证：提取 `# 7` 段统一替换 `input()` 后跑 19 个输入（四个方向的中文/小写/大写共 12 个、`跳`、空格、`攻击`、`j`、`J`、未知指令 `xyz`、`"\x1b"`），输出与预期逐条一致，`\x1b` 触发 break 正常结束；`py_compile` 通过。

## 2026-11-15 16:44

### 修复：`page/homework/section1/day2.py` 季度判断的 match 语法错误

- 现象：`py_compile` 报 `IndentationError: expected an indented block after 'case' statement (line 28)`。原写法把 `case 3:`、`case 4:`、`case 5:` 堆叠成空分支，而 Python 要求每个 `case` 后必须有缩进块，空 case 并非 fall-through（Python 的 `match` 不继承 C 的贯穿语义）。
- 修复：合并为选择模式（or-pattern）`case 3 | 4 | 5:`，四个季度分支各写成一行；`case 12 :` 的多余空格一并去掉。
- 验证：`py_compile` 通过；把 `input()` 换成固定值后覆盖 0/1/3/5/6/9/12/13 八种输入，输出依次为 异常/冬/春/春/夏/秋/冬/异常，符合预期。

## 2026-11-15 15:15

### 重构：`page/test1.py` 多级排序的 lambda 拆为独立函数

- `sorted(students, key=lambda x: (x['grade'], x['name']))` 中的匿名函数抽成模块级函数 `student_sort_key(student: dict) -> tuple[int, str]`，排序调用改为 `key=student_sort_key`。
- 好处：函数有名字和类型注解，堆栈和类型检查器都能直接定位；排序键逻辑与调用点分离，后续复用或改规则只改一处。
- 验证：`.venv/bin/python -m page.test1` 退出码 0，排序结果 `Alice(85), Charlie(85), Bob(92)`，与改动前一致。

## 2026-11-15 11:46

### 修复：`page/test1.py` 的计算器 match 分支

- 取消 `result = ""` 的预声明：初始空串从未被读取，每个分支都会覆盖它，判空时还会打印空行；改为在 `case _` 里也赋值，由 `case _` 保证所有路径都有值，`print(result)` 保持不变。
- 运算符变量 `c` 改名为 `op`，并由 `int(input())` 改为 `input().strip()`：原写法把运算符转成整数，永远匹配不上 `"+"` 等字符串，只能落到 `_` 分支。
- 修正 `case "+"` 里误写成 `a * b` 的加法。
- 输出格式去掉 `f"a {c} b = ..."` 里的字面量 `a`/`b`，改为拼接实际数值，如 `7 + 3 = 10`。
- 新增 `case "/" if b == 0` 守卫，避免除零抛 `ZeroDivisionError`。
- 验证：`+`、`/`、`/` 且除数为 0、非法运算符四种输入均输出正确；`ruff check` 未新增告警。

## 2026-11-15 11:12

### 新增：`page/lambda_typing.py`，演示 lambda 参数的类型推断写法

- 背景：lambda 语法不支持参数/返回值注解，本文件演示 5 种让类型检查器认识参数类型的写法：赋值时标注 `Callable`、函数参数提供上下文、内置高阶函数（`sort`/`map`）上下文、`cast` 强制标注、改用 `def`。
- 附演示 `functools.partial` 保留原函数注解，以及运行时事实：lambda 的 `__annotations__` 恒为空字典，`cast` 不写入注解。
- 修复演示代码中的一处类型问题：`int ** int` 被推断为 `Any`，`power` 改为 `int(base ** exp)` 以通过 `mypy --strict`。
- 验证：`.venv/bin/python page/lambda_typing.py` 退出码 0；`uvx mypy --strict` 0 报错；另写反例确认检查器能抓到 `f("hello")` 参数类型不符、`lambda s: s + 1` 在 `sort` 上下文中的 `str + int` 错误，以及无上下文 lambda 参数退化为 `Any`。

## 2026-11-14 21:27

### 重构：`page/enum_test.py` 改为导入 `enums/weekday_enum.py`，并修复全部告警

- 枚举定义不再重复写：删除文件内的 `WeekdayEnum`，改为 `from enums.weekday_enum import WeekdayEnum`，本文件只保留演示代码。
- 补全原来悬空的 `for item in WeekdayEnum:` 循环体（`IndentationError` 来源），遍历时打印值、成员名、中文名。
- 消除 PyCharm 告警：`_member_map_` 内部字典访问加 `# noinspection PyProtectedMember` 并用 `cast` 还原类型；`find(6)` 改为先取变量再判空，避免 `None` 成员取属性告警。
- 演示按模块枚举的现有能力改写：成员名用 `MON`/`FRI`/`SUN`，中文名用「星期X」；删掉依赖 `IntEnum` 的与 int 比较、排序及 `_missing_` 中文名兜底示例。
- 增加项目根目录 `sys.path` 引导，`python page/enum_test.py` 可直接运行。
- 验证：`python page/enum_test.py` 输出正常（退出码 0）；PyCharm 对 `page/enum_test.py`、`enums/weekday_enum.py` 均为 0 告警。
- 备注：编辑过程中 IDE 缓冲区曾把磁盘改动覆盖回去，导致类定义被删；已按完整内容恢复，后续改动建议先确认编辑器里该文件已无未保存修改。

## 2026-11-14 11:34

### 修复：`page/test1.py` 中 `DLog as print` 调用报错

- 现象：`from util.dlog import DLog as print` 后，`print(...)` 抛 `TypeError: DLog() takes no arguments`；文件末尾 `DLog.d(...)` 抛 `NameError`（别名后 `DLog` 名字不存在）。
- 修复 `util/dlog.py`：为 `DLog` 增加 `__init__(*args, sep=" ", end="\n")`，实例可像内置 `print` 一样多参数调用，输出仍走 DEBUG 格式并带调用位置；`_print_log` 增加 `end` 透传。
- 修复 `page/test1.py`：`DLog.d(f"list: {l}")` 改为 `print.d(...)`，与新别名保持一致。
- 验证：`PYTHONPATH=. .venv/bin/python -m page.test1` 全量输出正常，`-O` 模式下静默退出码 0；`page/comprehensions_demo.py` 回归正常。

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
