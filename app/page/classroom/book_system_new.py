import json
from abc import abstractmethod, ABC
from typing import TextIO

from mixins.repr_mixin import ReprMixin
from mixins.serializable_mixin import SerializableMixin


class BookNew(SerializableMixin, ReprMixin):
    """图书模型"""

    def __init__(self, book_id: str, title: str, author: str, total_num: int):
        self.book_id = book_id  # 书本编号
        self.title = title  # 书本名称
        self.author = author  # 作者
        self.total_num = total_num  # 书本总数
        self.__stock = total_num  # 书本库存（一开始默认等于总数）

    @property
    def stock(self) -> int:
        return self.__stock

    def stock_enough(self) -> bool:
        """还有库存"""
        return self.stock > 0

    def stock_add(self, num: int) -> None:
        """库存增加"""
        self.__stock += num


class MemberNew(SerializableMixin, ABC, ReprMixin):
    books: list[BookNew] = []  # 借阅列表：非构造参数，序列化时递归还原

    def __init__(self, member_id: str, name: str, password: str):
        self.member_id = member_id
        self.name = name
        self.password = password
        self.books = []

    @abstractmethod
    def max_borrow_count(self) -> int:
        pass

    def can_borrow_book(self) -> bool:
        """是否可以借书"""
        return len(self.books) < self.max_borrow_count()

    def book_borrow(self, book: BookNew) -> tuple[bool, str]:
        """从图书馆借书"""
        if not self.can_borrow_book():
            return False, "达到最大借书数量 "

        if not book.stock_enough():
            print("这本书没库存了")
            return False, '图书没有库存'

        self.books.append(book)
        book.stock_add(num=-1)
        return True, "借书成功"

    def book_back(self, book: BookNew) -> tuple[bool, str]:
        """还书"""
        for e in self.books:
            if e.book_id == book.book_id:
                self.books.remove(book)
                book.stock_add(num=1)
                return True, '还书成功！'
        return False, '没有借阅这本书！'


class NormalMemberNew(MemberNew, ReprMixin):

    def max_borrow_count(self) -> int:
        return 3


class VipMemberNew(MemberNew, ReprMixin):

    def __init__(self, member_id: str, name: str, password: str, vip_level: int):
        super().__init__(member_id, name, password)
        self.vip_level = vip_level

    def max_borrow_count(self) -> int:
        return 3 + self.vip_level


class LibraryNew(ReprMixin):
    BOOKS_JSON = "resources/book.json"  # 图书数据文件
    MEMBERS_JSON = "resources/member.json"  # 会员数据文件

    def __init__(self):
        self.books: dict[str, BookNew] = {}
        self.members: dict[str, MemberNew] = {}

        with open(self.BOOKS_JSON, "r+", encoding="utf-8") as f:
            items = json.load(f)
            if len(items) == 0:
                self.create_books_json(f)
                items = json.load(f)

            # 兼容列表与 {id: 对象} 两种存取格式
            rows = items.values() if isinstance(items, dict) else items
            for e in rows:
                self.books[e["book_id"]] = BookNew.from_dict(e)

        with open(self.MEMBERS_JSON, "r", encoding="utf-8") as f:
            items = json.load(f)
            if len(items) == 0:
                self.create_members_json(f)
                items = json.load(f)

            # 兼容列表与 {id: 对象} 两种存取格式
            rows = items.values() if isinstance(items, dict) else items
            for e in rows:
                member_cls = VipMemberNew if "vip_level" in e else NormalMemberNew
                self.members[e["member_id"]] = member_cls.from_dict(e)

        self.current_member: MemberNew | None = None  # 当前登录会员

    @staticmethod
    def create_books_json(f: TextIO) -> None:
        books: list[BookNew] = [
            BookNew(book_id="9787115546081", title="《Python编程》", author="埃里克·马瑟斯", total_num=5),
            BookNew(book_id="9787302587613", title="《C++程序设计》", author="谭浩强", total_num=3),
            BookNew(book_id="9787111213826", title="《Java编程思想》", author="布鲁斯·埃克尔", total_num=2),
            BookNew(book_id="9787302481447", title="《C程序设计》", author="谭浩强", total_num=1),
            BookNew(book_id="9787115545381", title="《JavaScript高级程序设计》", author="马特·弗里斯比", total_num=4),
        ]

        json.dump(books, f, ensure_ascii=False, indent=4, default=lambda o: o.to_dict())
        # a = json.load(f)
        # print(f"b: {a}")

    @staticmethod
    def create_members_json(f: TextIO) -> None:
        members: list[MemberNew] = [
            NormalMemberNew(member_id="N001", name="张三", password="668001"),
            NormalMemberNew(member_id="N002", name="李四", password="668002"),
            NormalMemberNew(member_id="N003", name="王五", password="668003"),
            VipMemberNew(member_id="V001", name="赵六", password="669001", vip_level=1),
            VipMemberNew(member_id="V002", name="钱七", password="669002", vip_level=2),
            VipMemberNew(member_id="V003", name="孙八", password="669003", vip_level=3),
            VipMemberNew(member_id="V004", name="周九", password="669004", vip_level=4),
        ]

        json.dump(members, f, ensure_ascii=False, indent=4, default=lambda o: o.to_dict())
        # a = json.load(f)
        # print(f"b: {a}")

    def login(self, name: str = "", password: str = "") -> MemberNew | None:
        while True:
            account = name.strip() or input("请输入会员名:")
            pwd = password.strip() or input("请输入密码:")
            target = self.members.get(account)
            if target is None:
                print("账号错误/用户未注册!")
                continue

            if pwd != target.password:
                print("密码输入错误")
                continue
            print("登录成功!")
            return target

    def book_borrow(self, count: int = 1) -> None:
        if self.current_member is None:
            print("请登录")
            return
        print("\n".join([f"{x}" for x in self.books.values()]))
        while True:
            book_id = input("请输入图书编号(每次一本):")

            if book_id not in self.books.keys():
                print("图书不存在!")
                continue

            target = self.books[book_id]
            if target.stock == 0:
                print(f"{target}暂无库存!")
                continue

            _, msg = self.current_member.book_borrow(target)
            print(msg)
            if count == 1:
                break

    def book_back(self) -> None:
        """还书"""
        if self.current_member is None:
            return

        self.book_look()
        book_id = input("请输入图书编号:")

        for e in self.current_member.books:
            if e.book_id == book_id:
                _, msg = self.current_member.book_back(e)
                print(msg)
                return

    def book_look(self) -> None:
        """查询图书借阅情况"""
        if self.current_member is None:
            return

        for book in self.current_member.books:
            print(f"图书编号 {book.book_id}, 书名: {book.title}, 作者: {book.author}")

        print(f"你一共借阅{len(self.current_member.books)}本书")

    def save_borrow_book(self) -> None:
        if self.current_member is None:
            return

        with open(self.MEMBERS_JSON, "w", encoding="utf-8") as f:
            json.dump(self.members, f, ensure_ascii=False, indent=4, default=lambda x: x.to_dict())

    def run(self) -> None:
        self.current_member = self.login(name="N002", password="668002")
        if self.current_member is None:
            return

        while True:
            print("*" * 60)
            print("\t".join(["1.借阅图书", "2.归还图书", "3.查看借阅", "4、退出系统", ]))
            print("*" * 60)

            op = input("请输入操作:")
            match op:
                case "1":
                    self.book_borrow()
                case "2":
                    self.book_back()
                case "3":
                    self.book_look()
                case "4":
                    self.save_borrow_book()
                    print("退出系统")
                    break
                case _:
                    print("无效的选项，请重新输入!")


if __name__ == "__main__":
    s = LibraryNew()
    s.run()
