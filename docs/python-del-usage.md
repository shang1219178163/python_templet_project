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

列表同理，删元素会让后续索引整体前移，漏删/越界：

```python
lst = [1, 2, 2, 3]
for i, v in enumerate(lst):
    if v == 2:
        del lst[i]      # ❌ 会漏掉一个 2

# 推荐：推导式重建
lst = [v for v in lst if v != 2]
```

## 七、函数里删全局名字

```python
name = "张三"

def clean():
    global name
    del name        # 必须声明 global，否则是删局部名字
```

## 速查表

| 场景 | 推荐写法 |
|---|---|
| 删列表某位置 | `del lst[i]` |
| 删一段 | `del lst[i:j]` |
| 清空但保留容器 | `del lst[:]` |
| 删字典键 | `del d[k]` / `d.pop(k, None)` |
| 删变量释放内存 | `del obj` |
| 删属性 | `del obj.attr` / `del Cls.attr` |
| 遍历中要删 | 先 `list(d)` 拷一份再删，或用推导式重建 |

一句话记忆：**`del` 删的是「名字」和「容器里的元素」，不删除对象本身；`len()` 会立刻感知，其他引用不会。**
