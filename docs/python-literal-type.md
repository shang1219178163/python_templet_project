# `Literal[...]`：类型注解里的字面量类型

## 一句话

`Literal[...]` 是 Python 类型注解里的 **字面量类型**：方括号里写的是 **允许的具体值本身**，不是类型。用来把参数或返回值限制成「只能是这几个值之一」。

## 项目里的实例

`app/base_widget/_layout.py`：

```python
from typing import Literal


def gap_token(spacing: float | str | None) -> Literal["small", "medium", "large"] | None:
```

含义：返回值只可能是 `"small"`、`"medium"`、`"large"` 或 `None` 四种，不可能是别的字符串。

`app/base_widget/flex.py`：

```python
def row(
    width: int | Literal["stretch", "content"] | None = None,
    height: int | Literal["stretch", "content"] | None = None,
): ...
```

含义：`width` / `height` 要么是整数，要么是 `"stretch"`，要么是 `"content"`，要么是 `None`。

写成 `int | str | None` 同样能通过，但 IDE 不知道 `"strtch"` 这类拼写错误是无意义的；`Literal` 能让 PyCharm / Ruff / mypy
当场标红。

## 关键点

### 1. 只给静态检查看，运行时完全不校验

```python
def set_align(x: Literal["left", "right"]) -> None: ...

set_align("center")   # IDE / ruff / mypy 报错，但 Python 照样运行
```

类型注解在运行时只是挂在函数上的一段元数据，不会拦截调用。

### 2. 方括号里只能写字面量

```python
Literal["a", "b"]       # ✅ 字符串
Literal[1, 2, 3]        # ✅ 整数
Literal[True, None]     # ✅ 布尔、None
Literal[WeekdayEnum.MONDAY]  # ✅ 枚举成员
Literal[some_var]       # ❌ 变量不行
Literal(str.upper())    # ❌ 表达式不行
```

### 3. 与 `str` 的区别

| 写法                   | 含义              | 传 `"abc"` |
|------------------------|-------------------|------------|
| `x: str`               | 任何字符串        | 允许       |
| `x: Literal["a", "b"]` | 只能是 `a` 或 `b` | 报错       |

### 4. 想让它在运行时真的生效

- **FastAPI / Pydantic**：`Literal` 会参与请求校验，传错值直接返回 422。这是 `Literal` 少数会在运行时起作用的场景。
- **普通函数**：得自己写判断。`_layout.py:11` 那句 `if spacing in ("small", "medium", "large")` 就是在做 `Literal`
  已经声明过、但运行时仍需手动完成的检查。

```python
def gap_token(spacing: float | str | None) -> Literal["small", "medium", "large"] | None:
    if spacing in ("small", "medium", "large"):  # 运行时的等价校验
        return spacing
```

### 5. `Literal` 还是 `Enum`

| 场景                                               | 选择                  |
|----------------------------------------------------|-----------------------|
| 几个固定字符串，只在参数里用一下                   | `Literal`，不用定义类 |
| 需要方法、需要遍历全部成员、需要序列化或数据库映射 | `Enum`                |

项目里 `app/enums/weekday_enum.py`、`app/enums/member_level_enum.py` 属于后者；`base_widget` 里那些只用于参数取值的字符串属于前者。

## 容易混淆的 `LiteralString`

`typing.LiteralString` 是 **另一回事**：它表示「这个字符串来自代码中的字面量，不是用户输入」，常用于防止 SQL 注入一类的检查。它和
`Literal[...]` 不是同一种东西，不要混用。

```python
from typing import LiteralString

def run_sql(sql: LiteralString) -> None: ...

run_sql("SELECT 1")         # ✅ 字面量
run_sql(user_input)         # ❌ 类型检查器报错（可能来自用户输入）
```

## 小结

- `Literal[值1, 值2, ...]` 约束 **取值集合**，不是约束类型。
- 默认只在静态检查阶段生效，运行时需要 Pydantic 或手写判断来兜底。
- 固定小集合的字符串参数优先用 `Literal`；需要更多行为时再升级成 `Enum`。
