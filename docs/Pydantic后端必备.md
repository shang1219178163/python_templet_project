# 后端开发中 Pydantic 要掌握到什么程度

## 结论

后端日常开发，Pydantic 掌握到「 **能定义请求/响应模型 + 拿到校验错误 + 序列化控制**」这一步就够了，大约覆盖 80% 的代码。
剩下 20% 遇到再查。

---

## 本项目依赖版本（据 `pyproject.toml`）

| 包                  | 版本约束    | 实际安装 | 对学习范围的影响                                                                  |
|---------------------|-------------|----------|-----------------------------------------------------------------------------------|
| `pydantic`          | `==2.14.2`  | 2.14.2   | 全部按 **V2** API 写：`model_validate` / `model_dump` / `model_config`            |
| `pydantic-settings` | `>=2.13.1`  | 2.13.1   | `BaseSettings`、`SettingsConfigDict` 从 `pydantic_settings` 导入，不从 `pydantic` |
| `pydantic-ai`       | `==2.65.0`  | 2.65.0   | 建在 Pydantic 之上的 Agent 框架，属于另一层，本文不涉及                           |
| `fastapi[standard]` | `>=0.162.0` | 0.162.0  | 原生支持 Pydantic V2，`response_model` 直接吃 `BaseModel`                         |
| `python`            | `>=3.13`    | 3.13.2   | 可以用 `type` 语句、PEP 695 泛型等新语法，模型注解写法不受限                      |

两点注意：

- `pydantic` 和 `pydantic-ai` 是 **`==` 锁定**，升级需要显式改 `pyproject.toml` 再 `uv lock`，不会被动漂移。
- 网上大量教程还是 V1（`.dict()`、`class Config`），跟本项目版本对不上，看到旧写法直接跳过。

---

## 第一层：必须熟练（不熟就没法写接口）

| 能力                                                                                                                | 项目里的现成例子                                                                        |
|---------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 用 `BaseModel` + 类型注解声明字段，带默认值即选填                                                                   | `app/model/book.py` 的 `Book`                                                           |
| 可变默认值必须用 `Field(default_factory=list)`                                                                      | `app/model/book_library.py` 的 `books`                                                  |
| 嵌套模型自动递归校验                                                                                                | `BookLibrary.books: list[Book]`                                                         |
| `model_validate(dict)` / `model_dump()` 在模型与字典间转换                                                          | `BookLibrary.load_books` 里的 `Book.model_validate(item)`                               |
| FastAPI 里模型即请求体/响应体：类型不符自动 422，不用手写校验                                                       | `app/api/book.py` 的 `-> list[Book]`，`/docs` 由模型自动生成                            |
| `Field(...)` 常用参数：`default_factory`、`ge/gt/min_length`、`pattern`、`alias` / `validation_alias`、`repr=False` | `app/model/book.py` 的约束写法；`app/model/student.py` 的 `name`、`library_password` |
| `Decimal` + `decimal_places` / `max_digits` 管金额精度                                                              | `app/model/book.py` 的 `price`                                                          |
| `model_config = ConfigDict(from_attributes=True)`：从 ORM/普通对象读取（接 SQLAlchemy 时必用）                      | 项目里还没有，接数据库就会用到                                                          |
| `Literal` / `Enum` / `X \| None` 表达有限取值与可空                                                                 | `member_level: MemberLevelEnum`                                                         |

**`pydantic-settings`** 在本项目已经是现成用法，直接看 `app/config.py`：

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    anthropic_model: str = "deepseek-chat"
```

- 字段名与环境变量名 **大小写不敏感地对应**（`anthropic_model` ↔ `ANTHROPIC_MODEL`）。
- 优先级：已存在的环境变量 > `.env` > 字段默认值。
- `extra="ignore"` 是必要的：`.env` 里还有 `PYTHONPATH` 等与配置类无关的键，不忽略会直接报校验错误。

---

## 第二层：应该知道（用到时不慌）

- **`model_config` 常用项**：`extra="forbid"`（拒绝多余字段）、`str_strip_whitespace=True`、`populate_by_name=True`、
  `frozen=True`。
  本项目两个都用上了：`Book` 开了 `str_strip_whitespace`，`Settings` 开了 `extra="ignore"`。
- **校验器**：`@field_validator` / `@model_validator`，处理「字段间依赖」这类规则（如结束时间 > 开始时间）。
- **序列化控制**：`model_dump(exclude={...}, by_alias=True, mode="json")` —— 返回给前端时排除密码、日期转成字符串。
- **`field_serializer`**：V2.14 的写法见 `app/model/book.py` 的 `_serialize_price`，用 `when_used="json"` 只影响 JSON 输出。
- **`Decimal` 的 JSON 序列化**：默认输出成 **字符串**（`"66.00"`），前端按字符串处理，需要数字要自己转换或写序列化器。
- **`ValidationError` 的结构**：`e.errors()` 返回 `loc/msg/type`，自定义 422 响应或记日志时要用。
- **判别联合（discriminated union）**：`Field(discriminator="type")`，做多形态消息/事件时比一串 `X | Y | Z` 准。
- **`computed_field`**：像 `Student.total_score` 那样写成 `@property` 不会出现在 JSON 里，要输出就得用
  `@computed_field`。

---

## 第三层：先跳过（知道名字即可，遇上再查）

`TypeAdapter`、`RootModel`、自定义类型与 `__get_pydantic_core_schema__`、泛型模型、`model_json_schema()` 生成、
strict 模式细节、性能调优、`pydantic.v1` 兼容模块、V1→V2 迁移历史。这些属于写库/写框架的人关心的层面。

---

## 三个最容易踩的坑

1. **必填 vs 选填**：`x: int` 是必填，`x: int = None` 在 V2 里会报错（要写 `x: int | None = None`）。
2. **V1 方法名全变了**：`.dict()` → `.model_dump()`、`.parse_obj()` → `.model_validate()`、`class Config` → `model_config`。
   本项目锁的是 2.14.2，网上旧教程一律以本文为准。
3. **响应模型会自动裁字段**：FastAPI 声明 `response_model` 后，多出来的字段不会返回 —— 别拿它当「过滤敏感字段」的唯一手段，
   源头上就该控制好模型的字段。

---

## 本项目现状与可选改进

- `Book` 已经把默认值全部换成 `Field(...)`：`ge=0` 管范围、`pattern` 管 ISBN 格式、`decimal_places=2` 管金额精度，
  字段说明写进 `description` 后会出现在 `/docs`。
- `Student` 同样全部换成 `Field(...)`：`student_id` / `name` 加 `min_length=1`，三科成绩加 `ge=0, le=100`；
  并用 `validation_alias=AliasChoices("name", "userName", "user_name")` 兼容多种字段名，`model_config` 开了
  `str_strip_whitespace`。这是第二层的内容，已经用上一半了。
- `Student.total_score` / `average_score` 目前是 `@property`，接口返回时不出现；需要输出的话改成 `@computed_field`。
- 配置统一在 `app/config.py`，其他模块只 `from app.config import settings`，不要再各自 `load_dotenv()`。
