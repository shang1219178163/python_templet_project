from functools import reduce

# 1
a = int(input("请输入数字:"))
print(f"{"odd" if a % 2 == 0 else "even"}")
print(f"{"成年" if a > 18 else "未成年"}")

if a > 0:
    print(f"a 是正数")
elif a < 0:
    print(f"a 是负的数")
else:
    print("a 是0")

# 2
if a >= 85:
    print(f"优秀, 保持")
elif 60 <= a < 85:
    print(f"及格, 需要努力")
else:
    print("不及格, 需要加倍努力")

# 6

match a:
    case 3 | 4 | 5:
        print(f"{a} 月春季")
    case 6 | 7 | 8:
        print(f"{a} 月夏季")
    case 9 | 10 | 11:
        print(f"{a} 月秋季")
    case 12 | 1 | 2:
        print(f"{a} 月冬季")
    case _:
        print("月份大于等于1 小于 12")

# 7
# 注意：input() 是"按回车提交"的，直接按下的 Esc 键会以 "\x1b" 送进来
# （想做到按一下立即响应，需要 curses / msvcrt / readchar 这类读取单键的库）
while True:
    action = input("请输入指令(esc 退出):")
    match action:
        case "上" | "w" | "W":
            print("角色向上移动")
        case "下" | "s" | "S":
            print("角色向下移动")
        case "左" | "a" | "A":
            print("角色向左移动")
        case "右" | "d" | "D":
            print("角色向右移动")
        case "跳" | " ":
            print("角色跳跃")
        case "攻击" | "j" | "J":
            print("角色发动攻击")
        case "退出" | "esc" | "ESC" | "\x1b":
            print("角色退出游戏")
            break
        case _:
            print(f"未知指令: {action!r}")

# 8
for i in range(a):
    print(i * "*")

# 9

# accounts = [
#     ("admin", "666888"),
#     ("root", "123456"),
#     ("zhangsan", "111111"),
# ]
#
# name = input("请输入用户名：")
# pwd = input("请输入密码：")
# count = 0
#
# if count < 5:
#     if (name, pwd) in accounts:
#         print("登录成功！")
#     else:
#         print("登录失败！")
#         count += 1
# else:
#     print("输入错误五次，不允许再操作了！")


# 10.
nums = list(range(0, a + 1, 5))
total = reduce(lambda x, y: x + y, nums)
print(f"total: {total}")

# 11
s = "akiwksjakdiklowiqaamnvbamvaxnsjdsjkaaxkjd"
target_list = list(filter(lambda x: x == "a" or x == "k", s))
print(f"target_list: {len(target_list)}")


# 12

def bank_ATM(money_total: float):
    tips = " ".join([
        "*" * 16,
        "1. 查询余额, 2. 存款, 3. 取款, 4. 退出",
        "*" * 16
    ])
    print(tips)

    while True:
        op = int(input("请输入操作:"))
        match op:
            case 1:
                print(f"当前余额: {money_total}")
            case 2:
                money_in = int(input("存款金额:"))
                money_total += money_in
                print(f"存款成功, 余额{money_total}")
            case 3:
                money_out = int(input("取款金额:"))
                if money_out <= money_total:
                    money_total -= money_out
                    print(f"取款成功, 余额{money_total}")
                else:
                    print(f"取款金额{money_out}不能超多总金额 {money_total}")
            case 4:
                print("退出系统")
                break


bank_ATM(9999)
