import random
import sys
from functools import reduce
from pathlib import Path

# 本文件在 lib/page/ 下，导入 lib 包需要先把项目根目录加入 sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lib.page.cheng_fa_biao import cheng_fa_biao, cheng_fa_biao_new
from lib.page.homework.section1.day1 import log_poetry

# from lib.util.dlog import DLog as print

print(f"Hello, World!")


#
#
# l = ["白日依山尽", "黄河入海流", "欲穷千里目", "更上一层楼"]
#
# for i, e in enumerate(l):
#     if e == l[0]:
#         print(f"# ######## #")
#         print(f"# {e} #")
#     elif e == l[-1]:
#         print(f"# {e} #")
#         print(f"# ######## #")
#     else:
#         print(f"# {e} #")
#
#
# print(int(True))
# print(int(False))
# print(None, type(None), None is None)
#
# print(f"list: {l}")
# print(f"list[0]: {l[0]}")
# print(1, 2, 3, sep=",", end="\n")
#
#
# a,b = 1, True
# print(f"a: {a}, b: {b}")
#
# # a,b = b,a
# # print(f"a: {a}, b: {b}")
#
#
# print(f"a: {a}, {isinstance(a, int)}, {type(a) is int}")
# print(f"b: {b}, {isinstance(b, bool)}, {type(b) is bool}")
#
#
# syms = ["\"", "\n", "\t", ]
# print(f"syms: {syms}")
#



# year = int(input("请输入年份："))
# year_run = (year % 100 != 0 and year % 4 == 0) or (year % 100 == 0 and year % 400 == 0)
# year_desc = "闰年" if year_run else "平年"
# print(f"{year}是{year_desc}！")
#
# cheng_fa_biao(9)
# cheng_fa_biao_new(9)





# a = int(input("a = "))
# b = int(input("b = "))
# c = int(input("c = "))

# if a + b > c or a + c > b or b + c > a :
#     if a == b == c :
#         print("等边")
#     elif a == b or b == c or c == a:
#         print("等腰")
#     else:
#         print("普通三角形")
# else:
#     print("非三角形")

#
# op = input("运算符(+ - * /)：").strip()
# match op:
#     case "+":
#         result = f"{a} {op} {b} = {a + b}"
#     case "-":
#         result = f"{a} {op} {b} = {a - b}"
#     case "*":
#         result = f"{a} {op} {b} = {a * b}"
#     case "/":
#         if b == 0:
#             result = "除数不能为 0"
#         else:
#             result = f"{a} {op} {b} = {a / b}"
#     case _:
#         result = f"暂不支持 {op}"
#
# print(result)


# n = 0
# while n < 3:
#     print(f"人生苦短,我用Python {n}")
#     n += 1
# else:
#     print("执行完毕!")


odds = [e for e in range(0, 100, 2) ]
sum1 = reduce(lambda x, y: x + y, odds)
print(f"odds {sum1}, {odds}")

# 多参数
nums1 = [1, 2, 3]
nums2 = [10, 20, 30]


def add(x: int, y: int) -> int:
    return x + y


result = list(map(add, nums1, nums2))
# result = list(map(lambda x, y: x + y, nums1, nums2))
print(result)  # [11, 22, 33]

# 多级排序
students = [
    {'name': 'Alice', 'grade': 85},
    {'name': 'Bob', 'grade': 92},
    {'name': 'Charlie', 'grade': 85}
]


def student_sort_key(student: dict) -> tuple[int, str]:
    return student['grade'], student['name']

sorted_students = sorted(students, key=student_sort_key)
# sorted_students = sorted(students, key=lambda x: (x['grade'], x['name']))
print(sorted_students)


def guess_num(min_num: int = 1, max_num = 100 ):
    random_num = random.randint(min_num, max_num)
    print(f"random_num: {random_num}")
    while True:
        val = int(input("输入数字(1-100):"))
        if val == random_num:
            print(f"恭喜成功 {val}")
            break
        elif val > random_num:
            print(f"猜大了")
        else:
            print(f"猜小了")

guess_num(1, 1000)