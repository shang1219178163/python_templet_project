from enums.base_enum import BaseEnum


class ReviewStatus(BaseEnum):
    PENDING = (0, "待审核", {"a": 1, })
    APPROVED = (1, "审核通过", {"b": 2})
    REJECTED = (2, "审核拒绝", {"c": 3, })


if __name__ == '__main__':
    # 1. 遍历成员：extra 是字典，call_extra() 原样返回
    for e in ReviewStatus:
        print([e.name, e.code, e.label, e.call_extra()])

    # 2. 查找
    print(ReviewStatus.code_of(2))  # <ReviewStatus.REJECTED: 2>
    print(ReviewStatus.name_of("APPROVED"))

    # 3. 数据型 extra：直接按键取值
    print(ReviewStatus.APPROVED.call_extra()["b"])  # 2

    # 4. 按补充数据条件查找
    print(ReviewStatus.match_of(lambda item: item.call_extra().get("b") == 2))

    # 5. 下拉框数据
    print(ReviewStatus.choices())

    # 6. 业务示例：审核通过后读取附加信息
    status = ReviewStatus.code_of(1)
    if status is ReviewStatus.APPROVED:
        print(f"审核通过，附加信息: {status.call_extra()}")
