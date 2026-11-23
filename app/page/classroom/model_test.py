from typing import Any


def printAddress(val: list[Any]) -> None:
    print("\n".join([f"{type(e)} {hex(id(e))}" for e in val]))


class ModelTest:

    def __init__(self,
                 dataNew: dict[str, Any] | None = None,
                 itemsNew: list[str] | None = None,
                 data: dict[str, Any] = {},
                 items: list[str] = [],

                 ) -> None:
        self.data = data
        self.items = items
        for e in [self.data, self.items]:
            print(f"{hex(id(self))} __init__ {type(e)} {hex(id(e))}")

        self.dataNew = dataNew
        self.itemsNew = itemsNew


a = ModelTest()
b = ModelTest()


# 0x10c7617f0 __init__ <class 'dict'> 0x10c6d5580
# 0x10c7617f0 __init__ <class 'list'> 0x10c6148c0
# 0x10c6b51d0 __init__ <class 'dict'> 0x10c6d5580
# 0x10c6b51d0 __init__ <class 'list'> 0x10c6148c0


def make():
    def inner(x=[]):
        x.append(1)
        return x

    return inner


i1, i2 = make(), make()
print(i1(), i2())  # [1] [1] ← 两次 def，各自独立

printAddress([i1(), i2()])
