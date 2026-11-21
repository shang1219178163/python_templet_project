# from app.util.dlog import DLog as print
from app.util.printdlog import printdlog as print


def calc_aeiou(s) -> list[str]:
    return [e for e in s if e in 'aeiouAEIOU']


def calc_score(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 1)


# 函数内可以直接访问到全局变量
def cal_tax(total_price):
    # tax_rate = 0.08 #如果定义了局部变量，优先使用局部变量
    # global tax_rate #用了global，可以修改全局变量，不修改也没问题,要在变量使用前标记
    # tax_rate = 0.08
    tax_rate = 0.08  # 没用global如果出现了赋值，说明整个丽数内部，用的都是局部变量，要先定义再使用
    print('函数内部变量值:', tax_rate)
    if total_price > 10000:
        tax = total_price * tax_rate
    elif total_price >= 5000:
        tax = total_price * tax_rate * 0.8
    else:
        tax = 0
    return tax


print(calc_aeiou('Hellow Python!'))  # ['e', 'o', 'o']

avg_score = calc_score([66, 77, 88.5, 99])
print(f"avg_score: {avg_score}")  # avg_score: 82.6
tax_rate = 0.05

my_tax = cal_tax(10000)
print(my_tax)
print(tax_rate)
