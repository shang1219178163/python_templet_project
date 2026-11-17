# `Callable` 上没有 `__code__`：装饰器里拿函数信息的正确类型注解

## 现象

装饰器内部访问 `func.__code__`，PyCharm / Pyright / mypy 报：

```
在 (...) -> Any 中找不到引用 __code__
Cannot access attribute "__code__" for class "Callable[..., Any]"
```

出错代码（`util/hook.py`）：

```python
from typing import Any, Callable

def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    code = func.__code__          # ⚠️ 类型检查报错
    filename = code.co_filename   # 定义所在文件
    lineno = code.co_firstlineno  # 定义所在行号
    func_name = code.co_name      # 函数名
```

## 根因

`Callable[..., Any]` 只承诺一件事：**这个对象可以被调用**（有 `__call__`）。
它不承诺有 `__code__`。

能放进 `Callable` 的类型比「普通函数」多得多：

| 对象 | 是否 `Callable` | 有 `__code__` |
| --- | --- | --- |
| `def` 出来的函数（`types.FunctionType`） | ✅ | ✅ |
| `functools.partial(f)` | ✅ | ❌ |
| 实现了 `__call__` 的类实例 | ✅ | ❌ |
| 类本身（`MyClass`） | ✅ | ❌ |
| 内置函数 / C 扩展函数（`len`、`print`） | ✅ | ❌ |
| `lambda` | ✅ | ✅（本质也是 FunctionType） |

`__code__` 只是 `types.FunctionType` 的专有属性，所以「在 `Callable` 上找不到它」是检查器的正确判断，不是误报。

## 修法一（推荐）：注解收窄为 `types.FunctionType`

```python
from functools import wraps
from types import FunctionType
from typing import Any, Callable

def decorator(func: FunctionType) -> Callable[..., Any]:
    code = func.__code__          # ✅ FunctionType 明确声明了 __code__
    filename = code.co_filename
    lineno = code.co_firstlineno
    func_name = code.co_name
```

优点：

- 类型定义里就有 `__code__`、`__name__`、`__defaults__`、`__annotations__`，全部可访问。
- 语义准确：这个装饰器本来就只支持真正的函数，传 `partial` 进去运行时会直接 `AttributeError`，注解提前把这一点写明。

代价：`@decorator` 不能用于 `functools.partial`、可调用实例等。如果你的确需要支持它们，走修法二。

## 修法二：保留 `Callable` 注解，用 `cast` 骗过检查器

```python
import types
from typing import Any, Callable, cast

def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    code = cast(types.FunctionType, func).__code__
```

`cast` 只在类型层面生效，运行时不改变任何东西。所以要清楚：

- 它没消除运行时风险，只是让检查器闭嘴。
- 若确实可能收到非函数对象，应显式兜底：

```python
code = getattr(func, "__code__", None)
if code is None:
    raise TypeError(f"{func!r} 不是普通函数，无法获取 __code__")
```

## 与 `dlog.py` 的对比

`util/dlog.py:72` 直接写 `DLog._print_log.__code__.co_filename`，没有报错——因为那里访问的是一个**具体函数对象**，类型是确定的 `FunctionType`，不是宽泛的 `Callable`。

同类问题只出现在「参数被注解成 `Callable` 之后又要访问函数专有属性」的场景。

## 验证

```bash
python3 util/hook.py
```

输出不变：

```
[before add args=(1, 2), kwargs={}]
[after  add args=(1, 2), kwargs={}]: 3
3
```

PyCharm 检查该文件：原报错消失，仅剩「局部变量未使用」弱警告（`filename`、`lineno`、`func_name`、`e`）。

## 延伸：装饰器里想拿函数信息，还有哪些写法

不一定非得碰 `__code__`，标准库 `inspect` 更稳：

| 需求 | 推荐写法 | 备注 |
| --- | --- | --- |
| 函数名 | `func.__name__`（配 `@wraps` 保留） | `partial` 没有，可用 `getattr` |
| 定义所在文件 | `inspect.getsourcefile(func)` | 对 C 函数返回 `None`，不抛异常 |
| 定义行号 | `func.__code__.co_firstlineno` | 无纯 inspect 等价物 |
| 参数列表 | `inspect.signature(func)` | 对内置函数也有效，装饰器校验参数首选 |
| 原始源码 | `inspect.getsource(func)` | 交互式环境可能失败 |
| 调用方位置 | `inspect.stack()[1]` / `sys._getframe(1)` | 想在日志里标「谁调用的」时用，`DLog` 即此思路 |

`inspect.signature` 是「只关心参数」时最安全的入口：它不会因为你拿到的是可调用实例而崩。
