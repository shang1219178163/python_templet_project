class Parent1:
    def func1(self) -> None:
        print(f"Parent1 func1")

    def func2(self) -> None:
        print(f"Parent1 func2")


class Parent2:
    def func1(self) -> None:
        print(f"Parent2 func1")

    def func2(self) -> None:
        print(f"Parent2 func2")


class Children(Parent1, Parent2):
    pass


child = Children()
child.func1()
child.func2()

# MRO = Method Resolution Order(方法解析顺序),找到第一个就停。
print(Children.mro())
