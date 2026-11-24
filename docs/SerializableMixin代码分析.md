# SerializableMixin 代码分析

- **分析对象**：`app/mixins/serializable_mixin.py`（86 行，仅标准库）
- **分析日期**：2026-11-24
- **关联用法**：`app/page/classroom/book_system_new.py`

## 一、结论

轻量级的模型 ↔ 字典转换 mixin：`to_dict` 反射实例字段并剥掉私有属性的名字修饰，`from_dict` 按 `__init__` 形参构造、其余字段回填。修复了「导出有 `stock`、导入丢掉 `stock`」的单向缺陷，`Optional` 与常见容器也能按注解还原。

## 二、实现结构

| 部分 | 作用 |
|---|---|
| `_dump` | 模型 → `to_dict()`；`list/tuple/set/frozenset/dict` 递归 |
| `_decode` | 按注解还原 `Optional/Union`、`list`、`dict`、`tuple` 与嵌套模型 |
| `to_dict` | 遍历 `vars(self)`，剥掉 `_类名__` 前缀，按 `exclude` 过滤 |
| `from_dict` | 形参过滤构造；私有属性与类注解字段回填；`strict` 校验未知字段 |

## 三、关键修复

1. **私有字段往返丢失**：`from_dict` 对构造器之外的字段，用 `_{cls.__name__}__{k}` 找底层属性并直接赋值，绕过只读 `property`。`BookNew.__stock` 借阅后重载不再回退。
2. **Optional / 容器不还原**：`_decode` 增加 `Union/Optional`、`dict`、定长 `tuple`、`tuple[T, ...]` 分支。
3. **未知字段静默丢弃**：新增 `strict=True`，列出无法归属的键并抛 `ValueError`；默认保持宽松。

## 四、刻意不做的扩展

以下能力按需再加，避免 mixin 膨胀：

- 日期、`Enum`、`Decimal` 与 JSON 类型互转；
- 循环引用检测；
- `__slots__` 类与父类私有字段支持；
- 类注解缓存、`ClassVar` 过滤。

## 五、验证

隔离脚本（`python -I`）覆盖私有字段往返、`exclude`、`list/Optional/dict/tuple` 还原、`strict`，全部通过。真实图书数据借阅列表 `stock=[3, 2]` 往返前后一致，VIP 子类正确还原；PyCharm lint 零警告。

```python
import sys

sys.path.insert(0, "/path/to/python_templet_project/app")
from mixins.serializable_mixin import SerializableMixin


class Book(SerializableMixin):
    def __init__(self, book_id: str, total_num: int):
        self.book_id = book_id
        self.total_num = total_num
        self.__stock = total_num

    @property
    def stock(self) -> int:
        return self.__stock

    def take(self) -> None:
        self.__stock -= 1


b = Book("A1", 5)
b.take()
data = b.to_dict()
assert data == {"book_id": "A1", "total_num": 5, "stock": 4}
assert Book.from_dict(data).stock == 4

try:
    Book.from_dict({**data, "typo": 1}, strict=True)
except ValueError as e:
    print("strict:", e)
```
