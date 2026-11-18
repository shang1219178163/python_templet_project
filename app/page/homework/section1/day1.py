#
# name = "小明"
# age = 18
# job = "学生"
# hobby = "打游戏"
# print("姓名: %s, 年龄: %s, 职业: %s, 爱好: %s" % (name, age, job, hobby))
# print(f"姓名: {name}, 年龄: {age}, 职业: {job}, 爱好: {hobby}")
#
#
# #
# # money_total = 10000
# #
# # pwd = input("请输入密码：")
# # print("密码正确！")
# # num = int(input("请输入取款金额："))
# # result = money_total - num
# # print(f"取款金额: {num}, 余额: {result}")


def log_poetry(items: list[str]) -> None:
    """打印诗词"""
    target = sorted(items, key=len)
    max_count = len(target[-1])
    # print(f"max_count: {max_count}")

    for i, e in enumerate(items):
        padding = (max_count - len(e) - 1) // 2 * '  '
        if i in [0, 2]:
            print(f" {'* ' * max_count}")
            print(f" * {padding}{e}{padding} * ")
        elif i == len(items) - 1:
            print(f" * {padding}{e}{padding} * ")
            print(f" {'* ' * max_count}")
        else:
            print(f" * {padding}{e}{padding} * ")


l1 = [
    "《登高》",
    "唐・杜甫",
    "风急天高猿啸哀，渚清沙白鸟飞回。",
    "无边落木萧萧下，不尽长江滚滚来。",
    "万里悲秋常作客，百年多病独登台。",
    "艰难苦恨繁霜鬓，潦倒新停浊酒杯。",
]

log_poetry(l1)


# name = input("请输入姓名：")
# chinese = int(input("请输入语文成绩："))
# engnish = int(input("请输入英语成绩："))
# score_sum = chinese + engnish
# score_ave = round(score_sum / 2.0, 1)
# score_good = score_ave >= 85 or score_sum >= 180
# score_good_tips = "成绩优秀！" if score_good else ""
# print(f"{name},总分{score_sum}，平均分为{score_ave}，{score_good_tips}")


# ok_user = "1111"
# ok_pwd = "666888"
# user = input("请输入用户名：")
# pwd = input("请输入密码：")
# if user == ok_user and pwd == ok_pwd:
#     print(f"登录成功！")
# else:
#     print(f"登录失败！")