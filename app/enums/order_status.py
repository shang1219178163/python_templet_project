from enums.base_enum import BaseEnum


class OrderStatus(BaseEnum):
    PENDING = (0, "待支付")
    PAID = (1, "已支付")
    SHIPPED = (2, "已发货")
    COMPLETED = (3, "已完成")
    CANCELLED = (4, "已取消")


if __name__ == '__main__':
    # 1. 遍历成员
    for e in OrderStatus:
        print([e.name, e.code, e.label])

    # 2. 查找
    print(OrderStatus.code_of(1))  # <OrderStatus.PAID: 1>
    # print(OrderStatus(1))  # 按 value（即 code）查找
    print(OrderStatus.name_of("SHIPPED"))  # <OrderStatus.SHIPPED: 2>
    print(OrderStatus.__members__.get("SHIPPED"))  # 按 value（即 code）查找

    # 3. 未设置 extra：call_extra 返回 None，无需判空或 getattr
    print(OrderStatus.PAID.call_extra())  # None

    # 4. 条件查找
    print(OrderStatus.match_of(lambda item: item.code >= 3))

    # 5. 下拉框数据
    print(OrderStatus.choices())
