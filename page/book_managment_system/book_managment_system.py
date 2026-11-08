from model import book_library_model

library = book_library_model.BookLibraryModel()


def main():
   print("######################## 欢迎使用图书管理系统 ##############")


def login():
    account = input("请输入账号:")
    pwd = input("请输入密码:")

    if account != "admin" or pwd != "123456":
        print("用户名或密码错误!")
        login()
        return          # 现在合法：退出 login 函数

    print("登录成功")


def print_borrowed_books():
    """打印当前借阅的图书列表"""
    borrowed_books = [(book.title, book.isbn) for book in library.books if book.is_borrow]
    if not borrowed_books:
        print("您当前没有借阅的图书。")
        return

    print(f"当前借阅的图书列表: {borrowed_books}")


main()
# 初始化图书馆模型
library.load_books(count=10)
book_titles = [f"{library.books.index(book)},{book.title},{book.isbn}" for book in library.books]
print(f"图书馆藏书列表:\n{'\n'.join(book_titles)},共{len(library.books)}本")

# 登录
# login()

print("""
######################## 欢迎使用图书管理系统 ##############
#                                                       #
#       1.借书  2.还书  3.查询我的借阅图书  4.退出系统       #
#                                                       #
######################## 欢迎使用图书管理系统 ###############
""")

while True:
    action = int(input("请输入操作选项:"))
    match action:
        case 1:
            isbn = input("借书->请输入图书编号:")
            target = next((e for e in library.books if e.isbn == isbn), None)
            # print(f"借书->target: {target.title}, {target.is_borrow}" if target else "借书->target: None")

            if target is None:
                print("无效的图书编号!")
            elif target.is_borrow:
                print(f"借书->图书 {target.title} 已被借出!")
            else:
                success = library.borrow_book(target)
                if success:
                    print(f"借书->成功: {target.title} by {target.author}")
                    print_borrowed_books()
                else:
                    print(f"借书->失败: {target.title} by {target.author}")
        case 2:
            isbn = input("还书->请输入要归还的图书编号:")
            target = next((e for e in library.books if e.isbn == isbn), None)
            # print(f"还书->target: {target.title}, {target.is_borrow}" if target else "还书->target: None")

            if target is None:
                print("还书->无效的图书编号!")
            elif not target.is_borrow:
                print(f"还书->图书 {target.title} 未被借出!")
            else:
                library.return_book(target)
                print_borrowed_books()
        case 3:
            print_borrowed_books()
            # print(f"借书记录->我的借阅图书: {[(e.title, e.isbn) for e in library.books if e.is_borrow]}")
        case 4:
            print(f"退出系统")
            break
        case _:
            print("无效的选项，请重新输入!")