"""
    案例:
    开发一个购物车管理系统，实现商品信息的添加、修改、删除、查询和统计功能。
    系统使用嵌套字典结构存储商品数据，通过控制台菜单与用户交互。
    具体功能如下：
        1. 添加购物车：用户根据提示录入商品名称、以及该商品的价格、数量，保存该商品信息到购物车。
        2. 修改购物车：要求用户输入要修改的购物车商品名称，然后再提示输入该商品的价格、数量，输入完成后修改该商品信息。
        3. 删除购物车：要求用户输入要删除的购物车名称，根据名称删除购物车中的商品。
        4. 查询购物车：将购物车中的商品信息展示出来，格式为："商品名称: xxx, 商品价格: xxx, 商品数量: xxx"。
        5. 退出购物车

    结构: shopping_cart = {"Meta80": {"price": 6999, "num": 2}, "鼠标": {...}}
"""

from typing import Any

# 商品名 -> {"price": 价格, "num": 数量}
shopping_cart: dict[str, dict[str, Any]] = {}
menu = """
####################### 购物车系统 #######################
#         1.添加  2.修改  3.删除  4.查询  5.退出           #
#########################################################
"""


def read_price() -> float:
    """读取价格，非法时要求重新输入"""
    while True:
        price = float(input("商品价格：").strip())
        if price is not None and price > 0:
            return price
        print("价格必须是非负数字，请重新输入")


def read_num() -> int:
    """读取数量，非法时要求重新输入"""
    while True:
        num = int(input("商品数量：").strip())
        if num is not None and num > 0:
            return num
        print("数量必须是非负整数，请重新输入")


def read_name() -> str:
    """读取商品名称，空名称直接返回空串，由调用方拒绝"""
    return input("商品名称：").strip()


def add_item() -> None:
    """添加商品：名称已存在时拒绝，避免覆盖原有数据"""
    name = read_name()
    if name in shopping_cart.keys():
        print("商品已存在,请执行修改操作")
        return
    shopping_cart[name] = {"price": read_price(), "num": read_num()}


def update_item() -> None:
    """修改商品：只允许修改已存在的商品"""
    name = read_name()
    if name not in shopping_cart.keys():
        print("商品不存在,请执行新增操作")
        return
    shopping_cart[name] = {"price": read_price(), "num": read_num()}


def delete_item() -> None:
    """删除商品：先判断存在，再用 del 按 key 删除"""
    name = read_name()
    if name not in shopping_cart.keys():
        print("商品不存在")
        return
    shopping_cart.pop(name)


def show_cart() -> None:
    """查询商品：遍历 items()，名称是 key，价格数量在 value 字典里"""
    if not shopping_cart:
        print("暂无商品")
        return

    for k, v in shopping_cart.items():
        print(f"{k}: {v}")


def run():
    # 循环次数不确定，用 while True，由用户选择 5 退出
    while True:
        print(menu)
        oper = input("请输入对应操作编号（1-5）:").strip()
        # 用户输入是单个值，值匹配优先用模式匹配 match case
        match oper:
            case "1":
                add_item()
            case "2":
                update_item()
            case "3":
                delete_item()
            case "4":
                show_cart()
            case "5":
                print("退出成功，欢迎下次使用！")
                break
            case _:
                print("不支持该操作！")


if __name__ == "__main__":
    run()
