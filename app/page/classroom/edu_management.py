class Student:

    def __init__(self, name: str, chinese: float, match: float, english: float) -> None:
        self.name = name
        self.chinese = chinese
        self.match = match
        self.english = english

    def __repr__(self) -> str:
        return f"{self.__dict__}"


class EduManagement:

    def __init__(self, data: dict[str, Student] | None = None) -> None:
        self.data = data or {}  # 每调一次，新建一个 {}
        # print(f"{hex(id(self))} __init__ {type(self.data)} {hex(id(self.data))}")

    def add(self):
        """修改"""
        name = input("请输入名称:")
        if name in self.data:
            print("数据已存在,请重新录入")
            return

        chinese = int(input("语文成绩:"))
        match = int(input("数学成绩:"))
        english = int(input("英语成绩:"))
        self.data[name] = Student(name=name, chinese=chinese, match=match, english=english)
        print(f"已添加成功 {name}")

    def update(self):
        """修改"""
        name = input("请输入名称:")
        if name not in self.data:
            print("数据不存在,请先录入")
            return

        chinese = int(input("语文成绩:"))
        match = int(input("数学成绩:"))
        english = int(input("英语成绩:"))
        self.data[name] = Student(name=name, chinese=chinese, match=match, english=english)

    def delete(self):
        name = input("请输入名称:")
        if name not in self.data:
            print("数据不存在,请先录入")
            return

        self.data.pop(name)

    def all(self):
        for k, v in self.data.items():
            print(k, v)

    def query(self, name: str = ""):
        if name == "":
            self.all()
            return

        if name not in self.data:
            print("数据不存在,请先录入")
            return

        targets = {k: v for k, v in self.data.items() if k == name}
        for k, v in targets.items():
            print(k, v)

    def run(self) -> None:
        while True:
            print("\n".join([
                "#######################################",
                "",
                "#1.添加 2.修改 3.删除 4.查询 5.查询所有 6.退出",
                "",
                "#######################################",
                ""
            ]))

            oper = input('输入对应操作(1-6):')
            match oper:
                case "1":
                    self.add()

                case "2":
                    self.update()

                case "3":
                    self.delete()
                case "4":
                    name = input("请输入名称:")
                    self.query(name)

                case "5":
                    self.query()

                case "6":
                    break
                case _:
                    print("异常操作")


EduManagement().run()
