import sys
from pathlib import Path

# 本文件在 app/page/ 下，导入 app 包需要先把项目根目录加入 sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.util.dlog import DLog

# print("hello world")
#
#
# print("##########")
# print("白日依山尽")
# print("黄河入海流")
# print("欲穷千里目")
# print("更上一层楼")
# print("##########")


# name = input("name:")
# age = input("age：")
# print(f"name is {name},age is {age}")

#
# total = 10000
#
#
# pwd = input("input pwd:")
# print(f"{pwd} right!!!")
#
# money = input("input money:")
# print(f"get money:{money} !")
#
# result = total - int(money)
# print(f"lease {result} money!")

#
# for i in range(3):
#     print(i)   # 输出 0, 1, 2

array = "a,b,c".split(",")
# array.append("d")
# print(f"array: {array}")

a = array.remove("b")
DLog.d(f"a: {a}")

b = array.pop(0)
DLog.d(f"b: {b}")

listA = [1, 2, 3]
listB = ["aa", "bb", "cc"]
listNew = [*listA, *listB]
DLog.d(f"listNew: {listNew}  type(listNew): {type(listNew)}")

listNewB = listA + listB
DLog.d(f"listNewB: {listNewB}  type(listNewB): {type(listNewB)}")

# listNew.sort()

contain = 'aa' in listB
DLog.d(f"listB contain aa: {contain}")

listNewANew = listA * 2
DLog.d(f"listNewANew: {listNewANew}")

rag = range(10)
arr1 = list(rag)
print(f"{rag} {type(rag)}, {arr1} {type(arr1)}")

dic = {"name": "王林", "age": 999, "hobby": "修炼升级"}
dic.pop("hobby")
print({k: v for k, v in dic.items()})

FloatOrInt = float


# 多入参单返回
def rectangle_area(l: float, w: float) -> float:
    """
    计算长方形面积
    :param l: 长
    :param w: 宽
    :return: 面积
    """
    _area = l * w
    return round(_area, 1)


print(rectangle_area(10, 50))


# 多返回
# 能够同时计算圆的面积和周长
def calc_circle(r: float) -> tuple[float, float]:
    _area = 3.14 * r * r
    _length = 2 * 3.14 * r
    return round(_area, 1), round(_length, 1)


area, length = calc_circle(10)
print(area, length)
