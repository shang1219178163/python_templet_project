# Python 里给方法加 `@property` 是什么意思

`@property` 是 Python 内置的 **属性装饰器**：它把一个方法「伪装」成属性 —— 调用时 **不写括号**，看起来像在读一个字段。

## 一、普通方法 vs 属性

```python
class Student:
    def total_score(self):  # 普通方法
        return self.chinese + self.math + self.english


s.total_score()  # 要加 ()
```

```python
class Student:
    @property
    def total_score(self):  # 属性
        return self.chinese + self.math + self.english


s.total_score  # 不加 ()
```

本项目里的现成例子：

- `app/model/student.py` 的 `total_score`：写成 `student.total_score`，不用 `student.total_score()`。
- `app/config.py` 的 `vision_model`：调用方读 `settings.vision_model` 时才计算「单独配了视觉模型就用它，否则回退默认模型」。

## 二、它解决了什么

1. **调用更自然**：`total_score` 本质是「算出来的值」而不是动作，不该长得像函数调用。
2. **对外伪装成字段**：外部代码 `s.total_score` 和 `s.chinese` 写法一致，不用关心背后是存储的还是计算的。
3. **实现可替换**：今天用 `@property` 现算，明天改成缓存字段或数据库查询，调用方代码一行不用改。
4. **读时计算**：`vision_model` 这类「依赖其他字段推导」的值，用 property 就不必再存一份可能过期的副本。

## 三、三个限制

### 1. 默认只读

没有配套的 `@xxx.setter` 时，`s.total_score = 100` 会抛 `AttributeError`。需要赋值就补：

```python
@total_score.setter
def total_score(self, value: int) -> None:
    ...
```

### 2. 在 Pydantic 模型里不算数据字段

`BaseModel` 中 `@property` 的值 **不会出现在 `model_dump()` 和 JSON 里**，也不参与校验。要让它出现在接口返回中，改用
`@computed_field`：

```python
from pydantic import computed_field


@computed_field
@property
def total_score(self) -> int:
    return self.chinese + self.math + self.english
```

装饰器顺序不能反：`@computed_field` 必须在 `@property` 上面。

### 3. 每次访问都会重新计算

计算昂贵（查库、读文件）时用 `functools.cached_property` 缓存；但它和 Pydantic 模型配合有坑（需要 `__dict__` 可写），一般先用普通
property，真的慢再优化。

## 四、选型速查

| 场景                               | 用什么                      |
|------------------------------------|-----------------------------|
| 由已有字段推导、无副作用、开销小   | `@property`                 |
| 需要出现在 JSON / 接口文档里       | `@computed_field`           |
| 要校验、要默认值、要序列化         | 声明成普通字段 `Field(...)` |
| 有副作用（写文件、发请求、改状态） | 普通方法，别伪装成属性      |

## 五、和本项目相关的两个具体动作

- `Student.total_score` 目前是 `@property`，接口返回时不出现；需要输出就改成 `@computed_field` + `@property`。
- `Settings.vision_model` 用 `@property` 是对的：它只是回退逻辑，不参与 `.env` 解析，也不该进序列化结果。
