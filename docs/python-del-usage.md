# Python `del` 使用场景总结

`del` 是**语句**，不是函数，作用只有一个：**删除「名字绑定」或「容器里的元素」**。它不负责销毁对象本身——只有当删除后没有任何引用指向该对象，对象才会被垃圾回收。

## 一、删除变量（名字绑定）

```python
a = 10
del a
print(a)        # NameError: name 'a' is not defined
```

```python
del x, y, z     # 一次删多个
```

**典型用途**：交互环境/脚本里清理临时变量、释放大对象（比如一个几百 MB 的 DataFrame），提前让 GC 回收。

注意：`del a` 只删了 `a` 这个名字，如果对象还有别的引用，对象依然活着：

```python
a = [1, 2, 3]
b = a
del a
print(b)        # [1, 2, 3]，列表没消失，只是少了一个名字
```

## 二、删除列表元素（最常用）

```python
nums = [10, 20, 30, 40, 50]

del nums[1]         # 按索引删 → [10, 30, 40, 50]
del nums[1:3]       # 按切片删 → [10, 50]
del nums[:]         # 清空但保留列表对象本身
del nums            # 整个列表名字删除
```

和 `pop()` / `remove()` / `clear()` 的对比：

| 操作 | 写法 | 说明 |
|---|---|---|
| 按下标删 | `del lst[i]` | 你知道位置，不需要返回值 |
| 按值删 | `lst.remove(v)` | 按值找，找不到报 `ValueError` |
| 弹栈删 | `v = lst.pop(i)` | 需要拿到被删的值 |
| 清空元素 | `del lst[:]` 或 `lst.clear()` | 保留 list 对象（其他引用能感知到变化） |
| 删整个变量 | `del lst` | 名字消失，其他引用不受影响 |

`del lst[:]` 和 `del lst` 的区别很关键：

```python
lst = [1, 2]
alias = lst
del lst[:]      # alias → []
# del lst       # alias → [1, 2]，列表还在
```

### `del` 与 `remove` 的完整对比

`del lst[i]` 按**位置**删，`lst.remove(v)` 按**值**删。

| 维度 | `del lst[i]` | `lst.remove(v)` |
|---|---|---|
| 定位方式 | 索引（位置） | 值（`==` 比较） |
| 语法属性 | **语句**，不是函数 | list 的**方法** |
| 返回值 | 无（`x = del lst[0]` 是语法错误） | `None` |
| 找不到时 | `IndexError` | `ValueError: list.remove(x): x not in list` |
| 重复元素 | 删指定那一个 | **只删第一个**匹配 |
| 批量删除 | ✅ 切片：`del lst[1:4]`、`del lst[::2]` | ❌ 一次一个 |
| 时间复杂度 | O(n-i)，后面元素前移 | O(n)，先查找再前移 |
| 支持负数索引 | ✅ `del lst[-1]` | 不涉及 |
| 是否原地修改 | ✅ 同一个 list 对象 | ✅ 同一个 list 对象 |

```python
lst = [10, 20, 30, 20]

del lst[1]          # 按位置 → [10, 30, 20]
lst.remove(20)      # 按值，删第一个 20 → [10, 30, 20]

del lst[1:3]        # 切片批量
del lst[::2]        # 带步长，对 [0,1,2,3,4,5] 删掉奇数位 → [0, 2, 4, 5]

[1, 2].remove(99)   # ValueError
del [1, 2][99]      # IndexError
```

实测输出：

```
remove 后: [10, 20] | 返回值: None
remove 找不到: list.remove(x): x not in list
del 越界: list assignment index out of range
```

#### 坑 1：`remove` 用 `==` 比较，NaN 会翻车

```python
nan = float("nan")
lst = [nan, 1]
lst.remove(float("nan"))   # ❌ ValueError —— nan != nan
```

CPython 的 `list.remove` 有身份捷径（先判 `x is y`），所以用**同一个对象**能删掉，换成新的 `float("nan")` 就删不掉：

```
新的 nan 对象 remove: list.remove(x): x not in list | 列表: [nan, 1]
同一 nan 对象 remove: [1]
```

同理，元素是自定义对象且 `__eq__` 写得有问题时，`remove` 行为跟着不可预期。`del` 只看下标，不受影响。

#### 坑 2：`remove` 只删第一个

```python
lst = [7, 7, 7]
lst.remove(7)
print(lst)    # [7, 7]
```

要删全部别循环 `remove`（每次都从头部重扫，O(n²)），用推导式重建：

```python
lst = [v for v in lst if v != 7]
```

#### 坑 3：遍历中删都会漏

```python
lst = [1, 2, 2, 3]
for i, v in enumerate(lst):
    if v == 2:
        del lst[i]
print(lst)   # [1, 2, 3]  ← 漏掉一个 2
```

`del` 和 `remove` 都会让后续元素前移，迭代器下标跟着错位。先拷贝再删，或直接用推导式。

#### 怎么选

| 情况 | 写法 |
|---|---|
| 知道下标 | `del lst[i]` |
| 知道值、且值唯一 | `lst.remove(v)` |
| 知道值、且要拿到被删的值 | `v = lst.pop(lst.index(x))` |
| 删一段 / 隔几个删一个 | `del lst[i:j]` / `del lst[::k]` |
| 删尾部 | `del lst[-1]` 或 `lst.pop()`（后者能拿到值） |
| 条件批量删 | `lst = [v for v in lst if not cond(v)]` |

#### 共同的注意点：都是原地修改

```python
a = [1, 2, 3]; b = a
del a[1]
print(b, a is b)   # [1, 3] True
```

任何持有同一列表引用的地方都会看到变化；而 `lst = [v for v in lst ...]` 是**换了新对象**，旧引用 `b` 仍指向旧数据。

## 三、删除字典键

```python
books = {"三体": {"price": 30}}
del books["三体"]        # 键不存在会 KeyError

books.pop("三体", None)  # 想「不存在也不报错」用 pop 带默认值
```

**这正是图书管理系统里该用的写法**——删除图书就应该是 `del books[book_name]`，而不是 `books[book_name] = None`（后者会让 `len(books)`、遍历统计都出错）。

## 四、删除对象/类的属性

```python
class Book:
    discount = 0.8          # 类属性

    def __init__(self):
        self.author = "刘慈欣"

b = Book()
del b.author                # 删除实例属性
print(b.author)             # AttributeError

del Book.discount           # 删除类属性（影响所有实例）
```

还有特殊方法：类里定义 `__del__`（析构函数），对象被回收前自动调用，但**不要依赖它的执行时机**。

## 五、删除导入的名字 / 模块级名字

```python
import os
del os          # 当前作用域内不能再直接用 os
```

常见于：脚本里执行完临时导入后清理，避免污染命名空间。

## 六、不能在遍历中删除

```python
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    del d[k]            # ❌ RuntimeError: dictionary changed size during iteration
```

**正确做法**（先拍快照）：

```python
for k in list(d):       # 或 d.copy()
    if k == "b":
        del d[k]
```

列表同理，删元素会让后续索引整体前移，漏删/越界——示例与推荐写法见上文「坑 3：遍历中删都会漏」。

## 七、函数里删全局名字

```python
name = "张三"

def clean():
    global name
    del name        # 必须声明 global，否则是删局部名字
```

## 八、`del` 与各类容器的移除方法对照

`del` 只做一件事：按**键或下标**从容器里摘元素。容器自己的方法（`remove` / `pop` / `discard` / `clear`）语义各有不同，下面放在一起对照。

### 总览

| 类型 | 按位置删 | 按值删 | 弹栈并取回 | 清空 | 删整个名字 |
|---|---|---|---|---|---|
| `list` | `del lst[i]`、`del lst[i:j]` | `lst.remove(v)` | `lst.pop(i)` | `del lst[:]` / `lst.clear()` | `del lst` |
| `dict` | `del d[k]` | — | `d.pop(k[, 默认])` / `d.popitem()` | `d.clear()` | `del d` |
| `set` | ❌ `del s[x]` 直接 `TypeError` | `s.remove(v)` / `s.discard(v)` | `s.pop()`（随机） | `s.clear()` | `del s` |
| `frozenset` | ❌ | ❌ | ❌ | ❌ | 不可变，只能换对象 |
| `str` | ❌ 不可变 | ❌ | ❌ | ❌ | 不可变，只能重建 |
| `tuple` | ❌ 不可变 | ❌ | ❌ | ❌ | 不可变，只能重建 |
| `deque` | `del dq[i]` | `dq.remove(v)` | `dq.pop()` / `dq.popleft()` | `dq.clear()` | `del dq` |
| `array.array` | `del arr[i]` | `arr.remove(v)` | `arr.pop(i)` | `arr.clear()` | `del arr` |

实测的三条硬性限制：

```
set 下标删除: 'set' object doesn't support item deletion
str del: 'str' object doesn't support item deletion
tuple del: 'tuple' object doesn't support item deletion
```

**只有 list / deque / array 这类有序可变序列支持 `del 容器[i]`**。set 无序没有下标，str / tuple / frozenset 不可变。

### dict：`del` 与 `pop` 的分工

```python
d = {"a": 1, "b": 2, "c": 3}

del d["a"]           # 无返回值；键不存在 → KeyError
d.pop("b")           # 返回 2；键不存在 → KeyError
d.pop("zz", "默认")   # 键不存在 → 返回 "默认"，不抛异常
d.popitem()          # 返回 ('c', 3)；3.7+ 后进先出（LIFO）
d.clear()            # {}
```

| 需求 | 写法 |
|---|---|
| 确定键存在，只是删 | `del d[k]` |
| 要拿到被删的值 | `d.pop(k)` |
| 键可能不存在，不想报错 | `d.pop(k, None)` |
| 删"最后进来的那个" | `d.popitem()` |

### set：`remove` 与 `discard`

```python
s = {1, 2, 3}

s.remove(1)      # {2, 3}
s.remove(99)     # ❌ KeyError: 99
s.discard(99)    # 静默返回 None，集合不变
s.pop()          # 随机删一个并返回；空集合 → KeyError
```

`remove` / `discard` 是 "按值删除" 的两种态度：前者严格（找不到就报错），后者宽容（找不到当没事发生）。`pop()` 删哪个由哈希顺序决定，**不要依赖具体元素**。

### str / tuple / frozenset：不可变，没有原地删除

```python
s = "abc"
s = s[:0] + s[1:]      # "bc"，靠切片重建，原字符串不受影响

t = (1, 2, 3)
t = t[:1] + t[2:]      # (1, 3)
```

注意区分：

```python
s = "abc"
del s          # ✅ 删的是名字 s，不是字符串内容
del s[0]       # ❌ TypeError
```

### deque：头删也是 O(1)

```python
from collections import deque

dq = deque([1, 2, 3])
dq.popleft()     # 1，O(1)
dq.pop()         # 3，O(1)
dq.remove(2)     # 按值，不存在 → ValueError
del dq[0]        # 按下标
```

对比 `list.pop(0)`：list 是连续数组，删头部要把后面全部前移 O(n)；deque 是双向队列，两端操作 O(1)。需要频繁从头部删时换 deque，函数名是 `popleft` 而不是 `pop(0)`。

### array.array：语法与 list 一致

```python
from array import array

arr = array("i", [10, 20, 30])
del arr[1]       # array('i', [10, 30])
arr.remove(10)
arr.pop(0)
arr.clear()
```

### 容易混的几点

| 易混点 | 说明 |
|---|---|
| 同名不同异常 | `list.remove` 找不到 → `ValueError`；`set.remove` 找不到 → `KeyError` |
| `pop()` 不带参 | list 删末尾、set 随机删、dict **必须给键**（`pop()` 会报 `TypeError`） |
| `clear()` vs `del x[:]` | 都是原地清空，其他引用看得见；`x = []` 是换对象 |
| `clear()` vs `del x` | 前者清空内容、名字还在；后者删名字、其他引用仍指向原对象 |
| 切片删除 | 只有 `del` 支持 `lst[i:j]`、`lst[::k]`，所有方法都不支持 |
| 删属性 | `del obj.attr` 等价于 `delattr(obj, "attr")`，见第四节 |

### 复杂度对照

| 操作 | 复杂度 |
|---|---|
| `list.pop()`（尾部） | O(1) |
| `del lst[i]` / `list.pop(i)` | O(n-i)，后面元素前移 |
| `deque.popleft()` / `deque.pop()` | O(1) |
| `dict` / `set` 的增删 | 平均 O(1) |
| `list.remove(v)` | O(n)，先扫描再前移 |
| 大列表按条件批删 | 推导式重建 O(n)，比循环 `remove` 的 O(n²) 好 |

## 速查表

| 场景 | 推荐写法 |
|---|---|
| 删列表某位置 | `del lst[i]` |
| 按值删列表元素 | `lst.remove(v)`（只删第一个，找不到抛 `ValueError`） |
| 删一段 | `del lst[i:j]` |
| 清空但保留容器 | `del lst[:]` |
| 删字典键 | `del d[k]` / `d.pop(k, None)` |
| 删变量释放内存 | `del obj` |
| 删属性 | `del obj.attr` / `del Cls.attr` |
| 遍历中要删 | 先 `list(d)` 拷一份再删，或用推导式重建 |

一句话记忆：**`del` 删的是「名字」和「容器里的元素」，不删除对象本身；`len()` 会立刻感知，其他引用不会。**
