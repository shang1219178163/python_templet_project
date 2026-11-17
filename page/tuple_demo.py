
students = (
    ("S002", "李慕婉", 92, 88, 95),
    ("S003", "+三", 78, 85, 82),
    ("S004", "曾牛", 88, 79, 91),
    ("S005", "周轶", 95,96, 89),
    ("S006", "王卓", 76, 82,77),
    ("S007", "红蝶", 89, 91,94),
    ("S008", "徐立国", 75, 69, 82),
    ("S009", "许木", 86, 89, 98),
    ("S010", "遁天", 66, 59, 72)
)
#1、每个学生信息拿出来, 进行计算for
# for student in students:

    # 方式2:解包
    #_解包接收单个元素, 后续不需要用到

def avg_score(scores) -> float:
    """求平均分，scores 为分数序列（元组/列表都可）"""
    return sum(scores) / len(scores)


def handle() -> None:

    for student in students:
        _, name, chinese, math, english = student
        total = chinese + math + english
        average = total / 3
        print(f'{student[1]}: {total}, #5: {round(average, 1)}')


    chinese_list = [e[2] for e in students]
    chinese_list_s = sorted(chinese_list)
    print(["chinese", chinese_list_s[0], chinese_list_s[-1]])

    math_list = [e[3] for e in students]
    math_list_s = sorted(math_list)
    print(["math", math_list_s[0], math_list_s[-1]])

    english_list = [e[4] for e in students]
    english_list_s = sorted(english_list)
    print(["english", english_list_s[0], english_list_s[-1]])

    better_list = [e for e in students if avg_score(e[-3:]) > 90]
    print(f"better_list: {better_list}")
    # print(f"better_list: {"\n".join(better_list)}")


handle()