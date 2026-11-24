# ORM 字段默认值 `default=` 使用示例

`default=` 是各 ORM 字段声明里的「应用层默认值」。下面按框架给示例，最后对比「何时生效」和常见坑。

## 一、SQLAlchemy 2.0

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employee"

    emp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    # 普通值默认
    base_salary: Mapped[float] = mapped_column(Float, default=5000.0)

    # 每次插入时调用函数（不要写成 default=datetime.now()）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # 可变默认值必须用可调用对象
    tags: Mapped[list[str]] = mapped_column(default=list)

    # 应用层 + 数据库层双保险
    status: Mapped[str] = mapped_column(
        String(10),
        default="active",                 # Python 侧，INSERT 时补值
        server_default=text("'active'"),  # DDL 里的 DEFAULT，绕过 ORM 直接插库也生效
    )
```

## 二、SQLModel / Pydantic

```python
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Employee(SQLModel, table=True):
    emp_id: str = Field(primary_key=True)
    name: str
    base_salary: float = Field(default=5000.0)
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)   # 可变值用 default_factory
```

Pydantic 的 `Field(default=...)` 在**对象一创建时**就生效，`Employee(name="张三").base_salary` 立刻是 `5000.0`。

## 三、Django ORM

```python
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    emp_id = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=50)
    base_salary = models.FloatField(default=5000.0)
    status = models.CharField(max_length=10, default="active", db_default="active")  # Django 5.0+
    created_at = models.DateTimeField(default=timezone.now)   # 传函数，别写 timezone.now()
```

注意：`default=timezone.now` 不带括号；写成 `timezone.now()` 会把「模块导入那一刻」固定成默认值。

## 四、Peewee

```python
from datetime import datetime

import peewee as pw


class Employee(pw.Model):
    emp_id = pw.CharField(primary_key=True, max_length=20)
    name = pw.CharField(max_length=50)
    base_salary = pw.FloatField(default=5000.0)
    created_at = pw.DateTimeField(default=datetime.now)
```

## 五、和普通类的对照

普通抽象类只能用**参数默认值**：

```python
def __init__(self, emp_id: str, name: str, base_salary: float = 5000.0):
    self.base_salary = base_salary
```

换成 dataclass 则是：

```python
from dataclasses import dataclass, field


@dataclass
class Employee:
    emp_id: str
    name: str
    base_salary: float = 5000.0
    tags: list[str] = field(default_factory=list)
```

三者的对应关系：`参数默认值` ↔ `dataclass field(default=...)` ↔ `ORM 字段 default=...`。

## 六、`default` 相关参数速查

| 写法 | 含义 | 典型用法 |
|---|---|---|
| `default=5000.0` | 应用层固定默认值 | 基本工资、状态字符串 |
| `default=函数/可调用对象` | 每次插入时调用一次 | `datetime.now`、`uuid4` |
| `default_factory=list` | 可变默认值（Pydantic/dataclass） | 列表、字典字段 |
| `default=list` | SQLAlchemy 对可变默认值的等价写法 | 列表、字典字段 |
| `server_default=...` | 数据库 DDL 默认，INSERT 省略该列时由库补值 | `text("5000")`、`func.now()` |
| `db_default=...` | Django 5.0+ 的数据库层默认 | 同上 |

## 七、两个容易踩的坑

### 1. 默认值的生效时机不同

| 框架 | 默认值何时出现 |
|---|---|
| Pydantic / SQLModel | 构造对象时 |
| Django | 构造对象时（`Model.__init__` 补默认值） |
| SQLAlchemy 普通映射 | **flush/INSERT 时**，`Employee().base_salary` 在写库前是 `None` |
| Peewee | 写库时 |

如果在 SQLAlchemy 里希望构造时就拿到默认值，可以改用 `MappedAsDataclass`：

```python
from sqlalchemy.orm import MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    pass
```

此时 `mapped_column(default=5000.0)` 会同时生成 dataclass 的构造参数默认值。

### 2. 可变默认值不能直接写 `[]` / `{}`

```python
tags = mapped_column(default=[])        # ❌ 所有实例共享同一个列表
tags = mapped_column(default=list)      # ✅ 每次插入新建列表
```

Pydantic/dataclass 侧同理，用 `default_factory=list`，而不是 `default=[]`。

## 八、在普通类与 ORM 模型之间的迁移

- 普通 Python 类：用参数默认值 `base_salary: float = 5000.0` 即可；
- 改成 ORM 模型时：删除构造器里的默认值，挪到字段上写 `default=5000.0`；
- 需要数据库层兜底（比如绕过 ORM 直接写库）：再加 `server_default` / `db_default`。
