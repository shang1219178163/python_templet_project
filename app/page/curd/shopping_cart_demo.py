"""
    案例:
    开发一个购物车管理系统，实现信息的添加、修改、删除、查询和统计功能。
    系统使用嵌套字典结构存储数据，通过控制台菜单与用户交互。
    具体功能如下：
        1. 添加购物车：用户根据提示录入名称、以及该的价格、数量，保存该信息到购物车。
        2. 修改购物车：要求用户输入要修改的购物车名称，然后再提示输入该的价格、数量，输入完成后修改该信息。
        3. 删除购物车：要求用户输入要删除的购物车名称，根据名称删除购物车中的。
        4. 查询购物车：将购物车中的信息展示出来，格式为："名称: xxx, 价格: xxx, 数量: xxx"。
        5. 退出购物车

    结构: shopping_cart = {"Meta80": {"price": 6999, "num": 2}, "鼠标": {...}}
"""

from collections.abc import Mapping

from app.util.console_crud import ConsoleCRUD, Field, Row


def format_item(name: str, row: Row) -> str:
    """单条展示：名称 + 价格 + 数量 + 小计"""
    price, num = row["price"], row["num"]
    return f"名称: {name}, 价格: {price}, 数量: {num}, 小计: {price * num}"


def summarize_cart(data: Mapping[str, Row]) -> str:
    """汇总行：合计金额"""
    return f"合计金额: {sum(r['price'] * r['num'] for r in data.values())}"


cart = ConsoleCRUD(
    title="购物车系统",
    entity="商品",
    name_prompt="商品名称：",
    fields={
        "price": Field("商品价格：", ConsoleCRUD.read_float),
        "num": Field("商品数量：", ConsoleCRUD.read_int),
    },
    format_row=format_item,
    summarize=summarize_cart,
    empty_hint="购物车为空",
)

if __name__ == "__main__":
    cart.batch_import({
        "Meta80": {"price": 6999, "num": 2},
        "鼠标": {"price": 199, "num": 3},
        "键盘": {"price": 299, "num": 1},
    })
    cart.run()
