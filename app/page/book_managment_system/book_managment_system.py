from app.model.book import Book
from app.model.book_library import BookLibrary


class BookManagementSystem:
    """图书管理系统"""

    ACCOUNT = "admin"
    PASSWORD = "123456"

    def __init__(self) -> None:
        self.library = BookLibrary()

    def run(self) -> None:
        print("######################## 欢迎使用图书管理系统 ##############")
        self.library.load_books(count=10)
        self.print_catalog()
        self.login()
        while True:
            self.print_menu()
            match self.read_action():
                case 1:
                    self.borrow_book()
                case 2:
                    self.give_back_book()
                case 3:
                    self.print_borrowed_books()
                case 4:
                    print("退出系统")
                    break

    def login(self) -> None:
        """账号密码错误时继续询问，避免递归登录把调用栈撑高"""
        while True:
            account = input("请输入账号:").strip()
            pwd = input("请输入密码:").strip()
            if account == self.ACCOUNT and pwd == self.PASSWORD:
                print("登录成功")
                return
            print("用户名或密码错误!")

    def print_menu(self) -> None:
        print("""
######################## 欢迎使用图书管理系统 ##############
#                                                       #
#       1.借书  2.还书  3.查询我的借阅图书  4.退出系统       #
#                                                       #
######################## 欢迎使用图书管理系统 ###############
""")

    def print_catalog(self) -> None:
        lines = [f"{index},{book.title},{book.isbn}" for index, book in enumerate(self.library.books)]
        print(f"图书馆藏书列表:\n{'\n'.join(lines)},共{len(self.library.books)}本")

    def print_borrowed_books(self) -> None:
        """打印当前借阅的图书列表"""
        borrowed_books = [(book.title, book.isbn) for book in self.library.books if book.is_borrow]
        if not borrowed_books:
            print("您当前没有借阅的图书。")
            return

        print(f"当前借阅的图书列表: {borrowed_books}")

    def read_action(self) -> int:
        """选项不在 1–4 时留在当前提示，直到输入有效指令"""
        while True:
            raw = input("请输入操作选项:").strip()
            if raw in {"1", "2", "3", "4"}:
                return int(raw)
            print("无效的选项，请重新输入!")

    def read_book(self, prompt: str) -> Book:
        """编号不存在时继续询问，不退回主菜单"""
        while True:
            target = self.library.find_book_by_isbn(input(prompt).strip())
            if target is not None:
                return target
            print("无效的图书编号，请重新输入!")

    def borrow_book(self) -> None:
        target = self.read_book("借书->请输入图书编号:")
        if target.is_borrow:
            print(f"借书->图书 {target.title} 已被借出!")
            return
        if self.library.borrow_book(target):
            print(f"借书->成功: {target.title} by {target.author}")
            self.print_borrowed_books()
            return
        print(f"借书->失败: {target.title} by {target.author}")

    def give_back_book(self) -> None:
        target = self.read_book("还书->请输入要归还的图书编号:")
        if not target.is_borrow:
            print(f"还书->图书 {target.title} 未被借出!")
            return
        if self.library.return_book(target):
            self.print_borrowed_books()
            return
        print(f"还书->失败: {target.title}")


if __name__ == "__main__":
    BookManagementSystem().run()
