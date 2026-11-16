# 1. 定义一个函数，根据传入的分数，计算对应的分数等级并返回。
#   1. 分数 >= 90：A
#   2. 分数 >= 75：B
#   3. 分数 >= 60：C
#   4. 分数 < 60：D
from datetime import datetime, timezone
from typing import Any


def score_level(v: float):
    match v:
        case v if v > 90:
            return "A"
        case v if v > 75:
            return "B"
        case v if v > 60:
            return "C"
        case _:
            return "d"


# score = float(input("请输入分数: "))
# level = score_level(v = score)
# print(f"level: {level}")


# 2. 定义一个函数，用于判断一个字符串是否是回文串，返回bool值。
#      把字符串反转，如果和原字符串相同，就是回文串。（如："level"，"radar"，"黄山落叶松叶落山黄"）

def is_hui(v: str):
    return v == v[::-1]


hui_test = "黄山落叶松叶落山黄"
print(f"{hui_test}是回文 ? {is_hui(v=hui_test)}")


# 3. 定义一个函数：完成时间转换功能，将传入的秒转换为小时、分钟、秒。
def second2datestr(v: int):
    year = v // (365 * 24 * 3600)
    rem = v % (365 * 24 * 3600)

    month = rem // (30 * 24 * 3600)
    rem %= (30 * 24 * 3600)

    day = rem // (24 * 3600)
    rem %= (24 * 3600)

    hour = rem // 3600
    rem %= 3600

    minute = rem // 60
    second = rem % 60

    result = f"{year}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return result


# ts = datetime.now().timestamp()

# 当前 UTC 时间的时间戳（推荐，避免时区歧义）
now = datetime.now(timezone.utc)
ts = int(now.timestamp())
dt = datetime.fromtimestamp(ts)

print([
    f"now {now},ts {ts}",
    second2datestr(v=ts),
    f"dt {type(dt)}, {dt}",
])


# 4. 定义一个函数：根据传入的三角形三个边的边长，判定三角形的类型（等边、等腰、普通，或者不能构成三角形）。


# 5. 定义一个函数，用于根据传入的一批商品信息（商品名、价格、数量）、优惠券、积分、运费
#        计算订单的总金额。
# - 具体规则如下：
#   1. 商品总金额
#     - 遍历所有传入的商品元组，将每个商品的 价格 × 数量 累加求和。
#   2. 优惠券扣减
#     - 使用条件：商品总金额 ≥ 5000 元才可以使用优惠券。
#     - 额度限制：优惠券金额不得超过商品总价（即不得让抵扣后金额为负数）。
#     - 不满足条件时，优惠券不生效。
#   3. 积分抵扣
#     - 使用条件：商品总金额 ≥ 5000 元才可以使用积分抵扣。
#     - 兑换比例：100 积分 = 1 元，积分只能整百抵扣（即实际抵扣金额 = score // 100）。
#     - 额度限制：积分抵扣金额不得超过商品总价。
#     - 不满足条件时，积分抵扣不生效。
#   4. 运费
#     - 直接累加到最终金额上，无任何限制。

def goods_total_amount(coupon: int=0, point: int=0, express: float=0.0):
    while True:
        name = input("商品名: ")
        price = float(input("价格: "))
        count = int(input("数量: "))

        price_sum = round(price * count, 2)
        price_sum_new = price_sum
        if price_sum >= 5000:
            coupon = float(input("优惠券: "))
            if coupon >= price_sum * 0.2:
                print("优惠券抵扣不能超过20%")
                continue
            price_sum_new = price_sum - coupon

            # 积分抵扣
            point = (price_sum // 100)
            if point >= price_sum:
                print(f"优惠券抵扣不能超过{point}")
                continue
            price_sum_new = price_sum - point

        desc = f"商品:{name} 价格:{price} 数量:{count}, {price_sum}(总价) - {express}(运费) - {coupon}(优惠券) - {point}(积分抵扣) + {express}(运费) = {price_sum_new}"
        print(desc)


# ============================================================================
# 练习1：智能数据筛选器
# ============================================================================
#
# 题目描述：
#   请设计一个通用数据筛选函数 filter_data，要求功能如下：
#   1. 通过 *args 接收任意数量的数值数据
#   2. 通过 **kwargs 接收筛选配置，支持的配置项包括：
#      - threshold：阈值，只保留大于等于该值的数据（默认：无阈值）
#      - top_n：只保留前N个（默认：全部保留）
#      - unique：是否去重（默认 False）
#      - sort_order：排序方式，"asc" 升序 / "desc" 降序（默认 "asc"）
#   3. 为所有函数添加完整的类型注解
#
#   测试：
#     filter_data(5,2,9,1,7,3,8,2,9,4, threshold=5, unique=True, sort_order="desc")
#       → [9, 8, 7, 5]
#     filter_data(3,5,1,8,6, top_n=3)
#       → [1, 3, 5]
# ============================================================================


def filter_data(*args:int, **kwargs: dict[str, str | int | bool]) -> list[int]:       # args -- 元组 ;  kwargs -- 字典    # print(f"args: {type(args)}, kwargs: {type(kwargs)}")

    threshold: int = kwargs.get("threshold", 1)
    top_n: int = kwargs.get("top_n", -1)
    unique: bool = kwargs.get("unique", False)
    sort_order: str = kwargs.get("sort_order", "asc")

    items = list(args)
    # print(f"items: {items}")
    if threshold != -1:
        items = list(filter(lambda x: x >= threshold, items))

    if top_n != -1:
        items = items[0:top_n]
        # print(f"items: {items}, top_n: {top_n}")

    if unique:
        items = list(set(items))
        # print(f"items: {items}, unique: {unique}")

    reverse = (sort_order == "desc")
    items = sorted(items, reverse=reverse)
    # print(f"items: {items}, sort_order: {sort_order}")

    print(items)
    return items


filter_data(5, 2, 9, 1, 7, 3, 8, 2, 9, 4, threshold=5, unique=True, sort_order="desc")
filter_data(3, 5, 1, 8, 6, top_n=3)


# ============================================================================
# 练习2：成绩统计分析器
# ============================================================================
#
# 题目描述：
#   设计一个函数 analyze_scores，要求功能如下：
#   1. 通过 *args 接收任意数量的分数（0~100之间的数值）
#   2. 通过 **kwargs 接收配置项：
#      - round_digits：结果保留的小数位数（默认 1）
#      - show_detail：是否打印详细信息（默认 False）
#      - pass_line：及格线分数（默认 60）
#   3. 返回值是一个字典，包含：
#      - count：人数
#      - max_score：最高分
#      - min_score：最低分
#      - avg_score：平均分
#      - pass_rate：及格率（以百分比字符串表示，如 "75.0%"）
#   4. 如果 show_detail=True，在函数内部打印详细统计信息
#   5. 如果未传入任何分数，返回字典中各项均为 0 或 "0%"
#   6. 添加完整的类型注解
#
#   测试：
#     analyze_scores(85,92,78,89,95,88,76,90, round_ndigits=2, show_detail=True)
#       → {'count': 8, 'max_score': 95, 'min_score': 76, 'avg_score': 86.62, 'pass_rate': '100.0%'}
#     analyze_scores(45,55,38,62,70,59, pass_line=60, round_ndigits=1)
#       → {'count': 6, 'max_score': 70, 'min_score': 38, 'avg_score': 54.8, 'pass_rate': '33.3%'}
# ============================================================================
def analyze_scores(*args: float, **kwargs: Any) -> dict[str, int | float | str]:
    # print(f"args: {type(args)}, kwargs: {type(kwargs)}")
    if len(args) == 0:
        return {
            "count": 0,
            "max_score": 0,
            "min_score": 0,
            "avg_score": 0,
            "pass_rate": "0%",
        }

    round_digits: int = kwargs.get("round_digits", 1)
    show_detail: bool = kwargs.get("show_detail", False)
    pass_line: float = kwargs.get("pass_line", 60.0)

    count: int = len(args)
    max_score: float = max(args)
    min_score: float = min(args)
    avg_score: float = round(sum(args) / count, round_digits)
    pass_rate: float = len(list(filter(lambda x: x >= pass_line, args))) / count

    result = {
        "count": count,
        "max_score": max_score,
        "min_score": min_score,
        "avg_score": avg_score,
        "pass_rate": f"{format(pass_rate, ".2%")}",
    }
    if show_detail:
        print(result)

    return result


report1 = analyze_scores(85, 92, 78, 89, 95, 88, 76, 90, round_digits=2, show_detail=True)
print(f"report1: {report1}")
report2 = analyze_scores(45, 55, 38, 62, 70, 59, pass_line=60, round_digits=1)
print(f"report2: {report2}")



# ============================================================================
# 练习3：个人信息卡片
# 知识点：默认参数 + 关键字参数 + **kwargs + 类型注解
# ============================================================================
#
# 题目描述：
#   设计一个函数 create_profile，用于生成个人信息卡片。要求如下：
#   1. 函数接收以下参数（均有默认值）：
#      - name：姓名（默认 "未填写"）
#      - age：年龄（默认 0）
#      - city：城市（默认 "未知"）
#      - job：职业（默认 "待业"）
#      - hobby：爱好（默认 "无"）
#   2. 除了上述参数外，还可以通过 **kwargs 接收任意自定义信息
#      （如 phone="138xxxx", email="abc@test.com"）
#   3. 函数返回一个格式化好的多行字符串（个人信息卡片），形如：
#      ===== 个人信息卡 =====
#      姓名: 张三
#      年龄: 25
#      城市: 北京
#      职业: 程序员
#      爱好: 篮球
#      --- 其他信息 ---
#      手机: 138xxxx
#      邮箱: abc@test.com
#      ======================
#   4. 添加完整的类型注解
#
#   测试：
#     create_profile("张三", 25, "北京", "程序员", "篮球",
#                    phone="138xxxx", email="abc@test.com")
#     create_profile("李四", city="上海", hobby="摄影")
#     create_profile()
# ============================================================================
def create_profile(name: str = "未填写",
                   age: int = 0,
                   city: str = "未知",
                   job: str = "待业",
                   hobby: str = "无",
                   **kwargs: str) -> str:
    """
     生成个人信息卡片

     :param name: 姓名
     :param age: 年龄
     :param city: 城市
     :param job: 职业
     :param hobby: 爱好
     :param kwargs: 其他自定义信息
     :return: 格式化的信息卡片字符串
     """

    # print(f"kwargs: {type(kwargs)} {kwargs}")


    lines = [
        "===== 个人信息卡 =====",
        f"姓名: {name}",
        f"年龄: {age}",
        f"城市: {city}",
        f"职业: {job}",
        f"爱好: {hobby}"
    ]

    if len(kwargs) != 0:
        lines.append("--- 其他信息 ---")
        for k, v in kwargs.items():
            lines.append(f"{k}: {v}")

    lines.append("======================")
    result = "\n".join(lines)
    print(result)
    return result

info1 = create_profile("张三", 25, "北京", "程序员", "篮球",
               phone="138xxxx", email="abc@test.com")

info2 = create_profile("李四", city="上海", hobby="摄影")
info3 = create_profile()
