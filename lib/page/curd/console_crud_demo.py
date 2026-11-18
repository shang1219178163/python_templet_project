"""ConsoleCRUD 组件使用示例：购物车。

演示三个可配置点：
    1. fields：用 Field 声明「提示语 + 读取函数」，添加/修改时按顺序录入；
    2. format_row / summarize：定制单条展示与汇总统计；
    3. data：传入初始数据，直接复用已有字典。

运行：python -m lib.page.curd.console_crud_demo
"""

from lib.util.console_crud import ConsoleCRUD, Field

# 商品名 -> {"price": 单价, "num": 数量}，作为初始数据
initial_cart: dict[str, dict[str, float | int]] = {
    "Meta80": {"price": 6999.0, "num": 1},
    "鼠标": {"price": 199.0, "num": 2},
}

cart = ConsoleCRUD(
    title="购物车系统",
    entity="商品",
    name_prompt="商品名称：",
    fields={
        "price": Field("商品价格：", ConsoleCRUD.read_float),
        "num": Field("商品数量：", ConsoleCRUD.read_int),
    },
    format_row=lambda name, row: (
        f"名称: {name}, 价格: {row['price']}, 数量: {row['num']}, 小计: {row['price'] * row['num']:.2f}"
    ),
    summarize=lambda data: f"合计金额: {sum(r['price'] * r['num'] for r in data.values()):.2f}",
    empty_hint="购物车为空",
    data=initial_cart,
)

if __name__ == "__main__":
    cart.run()
