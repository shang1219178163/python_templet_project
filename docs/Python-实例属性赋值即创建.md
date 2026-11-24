# Python 实例属性不必提前声明

`self.member_id = member_id` 能直接成立，是因为每个实例自带一个字典 `__dict__`。赋值就是往这个字典里插一条键，键不存在就新建，不需要事先在类上登记。

对应代码在 `app/page/classroom/book_system_new.py` 的 `MemberNew`。

## 一、实例先被造出来，属性后写进去

`NormalMemberNew("N001", "张三", "668001")` 实际是两步：

1. `__new__` 分配一个空实例。这时对象已经存在，`__dict__` 是 `{}`。
2. `__init__` 只是普通方法，往这个字典里填值。

所以这三行：

```python
self.member_id = member_id
self.name = name
self.password = password
```

等价于：

```python
self.__dict__["member_id"] = member_id
self.__dict__["name"] = name
self.__dict__["password"] = password
```

执行完之后，这个会员的 `__dict__` 是：

```python
{
    "member_id": "N001",
    "name": "张三",
    "password": "668001",
    "books": [],
}
```

`member_id` 这个名字从未出现在类体里，字典照样接受新键。类上没有一张「允许的字段表」供赋值去核对。

## 二、类体上的名字是另一份字典

`books: list[BookNew] = []` 写在类体里，进的是类的 `__dict__`，外加 `__annotations__`：

```python
MemberNew.__dict__["books"]         # []
MemberNew.__annotations__["books"]  # list[BookNew]
```

这是类属性，所有实例共享同一份，直到某个实例自己赋值。`__init__` 里的 `self.books = []` 会在该实例的 `__dict__` 里放一个新列表，之后 `m.books` 读到的是实例这份，类上那份被挡住。

读属性的顺序是：实例 `__dict__`，再类 `__dict__`，再父类。写属性时，默认直接写进实例 `__dict__`。

`stock` 那种 `@property` 是例外：类上有数据描述符时，赋值会走描述符的 `__set__`，写不进 `__dict__`。`MemberNew` 的这几个字段都没有描述符，所以赋值即创建。

## 三、注解不创建属性

`books: list[BookNew]` 这种注解只进 `__annotations__`，运行时不会因此出现 `self.books`。真正让每个会员拥有 `books` 的，是 `__init__` 里的 `self.books = []`。

类注解的作用是给 `SerializableMixin.from_dict` 的 `get_type_hints` 看：`books` 不是构造参数，还原时要按 `list[BookNew]` 把字典递归变成对象。见 `app/mixins/serializable_mixin.py`。

`from_dict` 分两步：

1. 只把 `__init__` 认识的字段传进构造函数。`member_id`、`name`、`password` 走这里，所以不必出现在类注解里。
2. 剩下的字段（比如 `books`）构造完再回填。回填时用类注解，才能知道每一项要还原成 `BookNew`。

```python
hints = get_type_hints(cls)
for k, v in data.items():
    if k in params:
        continue
    elif k in hints and not isinstance(getattr(cls, k, None), property):
        setattr(obj, k, _decode(hints[k], v))
```

没有 `books: list[BookNew]` 这条注解，JSON 里的借阅列表就只是普通字典，不会递归变成 `BookNew`。

类上的 `= []` 只是给注解一个占位，可以去掉，写成下面这样就够 `get_type_hints` 使用：

```python
books: list[BookNew]
```
