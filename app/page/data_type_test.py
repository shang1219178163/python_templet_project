from _pydecimal import Decimal
from collections import namedtuple

from util.dlog import DLog as print

print(Decimal(str(66.99)))  # Decimal('66.99')   ✅ 先转字符串)


def tuple_test():
    # 定义命名元组类型
    Person = namedtuple("Person", ["name", "age", "height"])
    # 创建对象
    person = Person("张三", 25, 1.75)
    # 通过索引访问
    print(person[0])  # 张三
    # 通过属性名称访问
    print(person.name)  # 张三
    print(person.age)  # 25
    print(person.height)  # 25


def jie_cheng(n: int) -> int:
    """阶乘(空间复杂度高)"""
    if n == 1:
        return n
    return n * jie_cheng(n - 1)


def jie_cheng_new(n: int) -> int:
    if n < 0:
        raise ValueError("n 必须是非负整数")
    result = 1
    for i in range(1, n + 1):
        # print(f"i:{i}")
        result *= i
    return result


print(jie_cheng_new(8))

tuple_test()
