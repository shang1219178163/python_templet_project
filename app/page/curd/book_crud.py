"""
【需求说明】
1. 业务背景
   使用面向对象思想，开发一个图书管理系统，对图书信息进行统一管理，
   支持添加、修改、删除、查询单本、查询所有等功能。

2. 涉及到的类
   2.1 Book（图书类）
       - 实例属性：书名(title)、作者(author)、价格(price)、库存(stock)
       - 方法：
           * __init__：初始化方法，创建图书对象时设置所有属性
           * __str__：返回图书的字符串表示，格式为：
             "书名: xxx | 作者: xxx | 价格: xxx | 库存: xxx"
           * update_info：支持更新图书的作者、价格、库存（书名作为唯一标识不可修改）

   2.2 BookSystem（图书管理系统类）
       - 类属性：system_name（系统名称）、system_version（系统版本号）
       - 实例属性：book_list（用于存放所有图书对象的列表）
       - 方法：
           * __init__：初始化方法，创建一个空的 book_list
           * add_book：添加一本新图书
           * update_book：修改指定图书的信息
           * delete_book：删除指定图书
           * query_book：查询指定图书
           * list_books：展示所有图书
           * run：显示菜单并循环接收用户操作

3. 业务规则
   3.1 添加图书时：
       - 依次输入书名、作者、价格、库存
       - 书名不能重复（已存在则提示并返回）
       - 价格必须大于 0，库存必须大于等于 0，否则提示并返回
   3.2 修改图书时：
       - 输入要修改的书名
       - 若不存在则提示"未找到该图书"
       - 找到后依次输入新的作者、价格、库存，并更新
   3.3 删除图书时：
       - 输入要删除的书名
       - 若不存在则提示"未找到该图书"
   3.4 查询图书时：
       - 输入书名进行精确查询
   3.5 展示所有图书时：
       - 遍历 book_list，依次输出每一本图书的信息

4. 菜单
       1. 添加图书   2. 修改图书   3. 删除图书
       4. 查询指定图书  5. 查询所有图书  6. 退出系统
"""

from collections.abc import Mapping

from app.util.console_crud import ConsoleCrud, CrudField, CrudRow


def format_row(title: str, row: CrudRow) -> str:
    return f"{title} {row}"


def summarize(data: Mapping[str, CrudRow]) -> str:
    sum_price = sum([e["price"] * e["stock"] for e in data.values()])
    return f"{len(data.keys())}本书价值总和: {sum_price}"


book_m = ConsoleCrud(
    title="图书管理系统",
    entity="图书",
    key_prompt="图书名称:",
    fields={
        "author": CrudField("作者: ", ConsoleCrud.read_str),
        "price": CrudField("价格: ", ConsoleCrud.read_float, lambda e: e > 0, "价格必须大于 0"),
        "stock": CrudField("库存: ", ConsoleCrud.read_int, lambda e: e >= 0, "库存大于等于0")
    },
    format_row=format_row,
    summarize=summarize,
    empty_hint="图书为空"
)

if __name__ == "__main__":
    book_m.run()
