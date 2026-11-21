from enums.base_enum import BaseEnum


class UserStatus(BaseEnum):
    ACTIVE = (1, "正常", lambda x: x + 1)
    DISABLED = (2, "禁用", lambda x: x + 2)
    DELETED = (3, "删除", lambda x: x + 3)


if __name__ == '__main__':
    # 1. 遍历成员：name / code / label / extra 计算结果
    for e in UserStatus:
        print([e.name, e.code, e.label, e.call_extra(100)])

    # 2. 三种查找方式
    print(UserStatus.code_of(2))  # <UserStatus.DISABLED: 2>，找不到返回 None
    print(UserStatus.code_of(99))  # None
    print(UserStatus(2))  # 按 value（即 code）查找
    print(UserStatus["DISABLED"])  # 按成员名查找，找不到抛 KeyError
    print(UserStatus.name_of("DISABLED"))  # 按名字查找，找不到返回 None

    # 3. 条件查找
    print(UserStatus.match_of(lambda item: item.label == "禁用"))

    # 4. extra 是函数：call_extra 直接调用，也可直接 e.extra(...)
    print(UserStatus.ACTIVE.call_extra(100))  # 101

    # 5. 序列化：value/code 是 int，入库或返回 JSON 时取 code
    print({"status": UserStatus.ACTIVE.code})  # {'status': 1}

    # 6. 下拉框数据：(code, label) 列表
    print(UserStatus.choices())

    # 7. 业务示例：接口入参 code 转枚举后判断
    status = UserStatus.code_of(2)
    if status is UserStatus.DISABLED:
        print("账号已禁用，不能登录")
