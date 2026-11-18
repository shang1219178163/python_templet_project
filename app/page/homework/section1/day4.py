# ----------------------------------------------------------
# 需求1：定义一个函数 is_leap_year，接收一个年份 year（整数），
#       判断该年份是否为闰年，返回 True 或 False。
#
#       闰年规则：
#         - 能被 400 整除的是闰年
#         - 能被 4 整除但不能被 100 整除的也是闰年
#         - 其余不是闰年
#
#       调用该函数，分别判断 2000年、2024年、1900年、2025年 是否为闰年。
# ----------------------------------------------------------

def leap_year(year: int):
    is_leap = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    return is_leap


for year in [2000, 2024, 1900, 2025]:
    print(f"{year} 是闰年吗?{leap_year(year)}")


# ----------------------------------------------------------
# 需求2：定义一个函数 count_case，接收一个字符串参数，
#       统计其中大写字母和小写字母的个数，返回两个结果。
#       （提示：可用字符串的 .isupper()判断是否为大写字母 和 .islower() 方法判断该字母是否为小写字母）
#
#       调用该函数，传入字符串 "Hello World! Python3 编程"，
#       用解包方式接收并打印大写字母个数和小写字母个数。
# ----------------------------------------------------------
def count_case(val: str):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    letters_upper = [e for e in val if e in letters]
    letters_lower = [e for e in val if e in letters.lower()]
    print(f"letters_upper: {letters_upper}, {len(letters_upper)}个字母")
    print(f"letters_lower: {letters_lower}, {len(letters_lower)}个字母")


count_case("Hello World! Python3 编程")

# dic = {"a" : {"count": 3}, "b" : {"count": 3}}
# for e in dic:
#     print(dic)
# exit()

# 1. 图书管理系统开发 【必做】
# 需求描述：
# 开发一个图书管理系统，在该系统中可以维护和管理图书信息，具体需求如下：
# 1. 添加图书信息：根据提示录入图书名称、作者、价格、库存数量，录入完成保存到系统中。
# 2. 修改图书信息：输入要修改的图书名称，然后再提示输入新的作者、价格、库存数量，输入完成后修改图书信息。
# 3. 删除图书信息：输入要删除的图书名称，根据名称删除图书信息。
# 4. 查询图书信息：输入要查询的图书名称，根据名称查询图书信息并输出。
# 5. 列出所有图书：遍历所有图书信息并输出。
# 6. 图书统计：统计图书种类数、库存总量、总价值（每本书价格×库存之和）、价格最高和最低的图书名称。
# 7. 退出系统。


"""
    案例：图书管理系统
    1. 添加图书信息：根据提示录入图书名称、作者、价格、库存数量，录入完成保存到系统中。
    2. 修改图书信息：输入要修改的图书名称，然后再提示输入新的作者、价格、库存数量，输入完成后修改图书信息。
    3. 删除图书信息：输入要删除的图书名称，根据名称删除图书信息。
    4. 查询图书信息：输入要查询的图书名称，根据名称查询图书信息并输出。
    5. 列出所有图书：遍历所有图书信息并输出。
    6. 图书统计：统计图书总数、库存总量、总价值、价格最高和最低的图书名称。
    7. 退出系统。
"""

menu = """
# # # # # # # # # # # # # # # # # # # # # # # 【图书管理系统菜单】 # # # # # # # # # # # # # # # # # #
#       1. 添加图书  2. 修改图书  3. 删除图书  4. 查询图书  5. 列出所有图书  6. 图书统计  7. 退出系统        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
"""
print("欢迎使用图书管理系统 ~")
print(menu)

# 使用字典存储图书，key=书名, value=包含作者、价格、库存的字典
book_dic = {
    "设计模式": {'author': '亚历山大', 'price': 66.0, 'count': 6},
    "python实战": {'author': '大神', 'price': 77.0, 'count': 7},
    "算法导论": {"author": "Thomas H. Cormen", "price": 55, "count": 2}
}

while True:
    action = int(input(
        "请选择操作(1. 添加图书  2. 修改图书  3. 删除图书  4. 查询图书  5. 列出所有图书  6. 图书统计  7. 退出系统):"))
    match action:
        case 1:
            # 添加图书
            book_name = input("图书名称:")
            book_author = input("图书作者:")
            book_price = float(input("图书价格:"))
            book_count = int(input("图书数量:"))
            book_dic[book_name] = {"author": book_author,
                                "price": book_price,
                                "count": book_count,
                                   }
            print(f"新增图书: {book_name}: {book_dic[book_name]}")

        case 2:
            # 修改图书
            book_name = input("图书名称:")
            if book_name not in book_dic:
                print(f"{book_name}不存在")
                continue

            print(f"{book_name}: 原信息 {book_dic[book_name]}")

            book_author = input("新图书作者:")
            book_price = float(input("新图书价格:"))
            book_count = int(input("新图书数量:"))
            book_dic[book_name]["count"] = book_count
            book_dic[book_name]["author"] = book_author
            book_dic[book_name]["price"] = book_price
            book_dic[book_name]["count"] = book_count
            print(f"{book_name}: 新信息 {book_dic[book_name]}")

        case 3:
            # 删除图书
            book_name = input("图书名称:")
            target = book_dic.get(book_name)
            if target is None:
                print(f"删除失败,{book_name} 不存在!")
                continue

            confirm = input("确认删除(Y/N):")
            if confirm in ["Y", "y"]:
                # del book_dic[book_name]
                book_dic.pop(book_name, None)
                print(f"{book_name}已删除!")

        case 4:
            # 查询图书
            book_name = input("图书名称:")
            target = book_dic.get(book_name)
            if target is None:
                print(f"{book_name} 不存在!")
                continue
            print(f"{book_name}: {target}")

        case 5:
            # 列出所有图书
            for k, v in book_dic.items():
                print(f">>{k}: {v}")

        case 6:
            # 图书统计：统计图书总数、库存总量、总价值、价格最高和最低的图书信息。
            total_category = len(book_dic)
            total_count = 0
            total_price = 0.0
            for k, v in book_dic.items():
                total_count += v["count"]
                total_price += v["price"] * v["count"]

            print(f"图书种类数 {total_category}")
            print(f"总数 {total_count}")
            print(f"总价值 {total_price}")

            # 转为元祖数组,价格倒序
            sorted_prices = sorted(book_dic.items(), key=lambda x: x[1]["price"], reverse=True)
            # print(f"sorted_prices  {type(sorted_prices)}, {sorted_prices}")
            price_max = sorted_prices[0]
            price_min = sorted_prices[-1]
            price_max_name, price_max_info = price_max
            price_min_name, price_min_info = price_min
            print(f"价格最高图书{price_max_name} {price_max_info["price"]}")
            print(f"价格最低的图书{price_min_name} {price_min_info["price"]}")

        case 7:
            # 退出系统
            exit()
