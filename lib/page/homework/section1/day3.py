from functools import reduce

# 1
# 合并如下三个列表，并对合并后的列表进行元素的去重，然后排好序后输出到控制台
list1 = ['M', 'A', 'C', 'E', 'F', 'G', 'H', 'L', 'N', 'I', 'J', 'K', 'O']
list2 = ['X', 'Z', 'T', 'Y', 'D', 'E', 'F', 'G']
list3 = ['W', 'A', 'S', 'D']


setTmp = {*list1, *list2, *list3}
print(f"setTmp {type(setTmp)}, {setTmp}")

set_tmp_new = sorted(list(setTmp))
print(f"set_tmp_new {set_tmp_new}")


# 2 将如下列表中能被3 或 5整除的元素提出来，并获取这些数字对应的平方，组成一个新的列表。
list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
list1_new = [e ** 2 for e in list1 if e % 3 == 0 or e % 5 == 0]
print(f"list1_new: {list1_new}")


# 3 将如下列表中的正数提取出来，封装为一个新的列表。
list2 = [11, 2, 31, 4, -5, 15, 17, 28, 49, 10, -11, 16, 54, -14, 36, -16, 87, -39]
list2_new = [e for e in list2 if e > 0]
print(f"list1_new: {list2_new}")

# 4. 输入一个字符串, 判断该字符串是否是回文(两边对称) 。
input_str = "黄山落叶松叶落山黄"
if input_str == input_str[::-1]:
    print(f'"{input_str}" 是回文（两边对称）')
else:
    print(f'"{input_str}" 不是回文')

# 5. 将用户输入的10个字符串, 反转后全部转换为大写, 然后记录在列表中, 最后将列表内容，遍历输出出来。

str_list = []
for i in range(3):
    s = input(f"请输入第{i + 1}个字符串: ")
    tmp = s[::-1].upper()
    str_list.append(tmp)

print(f"str_list: {str_list}")


# 6. 现有两个变量，分别为：a = 10， b = 20，现需要将这两个变量值交换，然后输出到控制台。
a = 10
b = 20
a, b = b,a
print(f"a: {a}, b: {b}")


# 7. 现有三个变量，分别为：a=100，b = 200，c = 300，现需要将这三个变量值进行交换，将 a,b,c 的值分别赋值给 c,a,b，并将其输出到控制台。
a = 100
b = 200
c = 300
c, a, b = a, b, c
print(f"a: {a}, b: {b}, c: {c}")


# 【题目】
# 已知两个班级的学员编号：
# class_a = [101, 102, 105, 108, 102, 110, 105, 112, 108]
# class_b = [105, 106, 108, 109, 111, 101, 113, 106]
#
# 请完成以下操作：
# 1. 合并两个列表的数据，得到合并后的原始列表 merged
# 2. 对 merged 进行列表去重，保留第一次出现的顺序，得到 unique_list
# 3. 使用列表推导式，从 unique_list 中筛选出所有的奇数编号，生成 odd_list，并输出
# 4. 使用列表推导式，odd_list 中每个元素在其基础上加 10000，生成 new_list，并输出


class_a = [101, 102, 105, 108, 102, 110, 105, 112, 108]
class_b = [105, 106, 108, 109, 111, 101, 113, 106]

merged = [*class_a, *class_b]
print(f"merged: {merged}")

unique_list = []
for e in merged:
    if e not in unique_list:
        unique_list.append(e)
print(f"2. 去重后（保留顺序）: {unique_list}")

odd_list = [e for e in unique_list if e % 2 == 0]
new_list = [e for e in unique_list if e % 2 != 0]
print(f"odd_list: {odd_list}")
print(f"new_list: {new_list}")


# 【题目】
# 已知四个课外活动小组的成员名单：
# calligraphy_set = {"王林", "曾牛", "天运子", "韩立", "厉飞雨", "紫灵", "徐立国"}
# painting_set    = {"张铁", "王林", "曾牛", "王蝉", "韩立", "厉飞雨", "云露", "李化元"}
# music_set       = {"许木", "红蝶", "韩立", "天运子", "厉飞雨", "曾牛", "虎咆"}
# sports_set      = {"遁天", "天运子", "韩立", "姜老道", "紫灵", "云露", "虎咆"}
#
# 请完成以下操作：
# 1. 找出同时参加了所有四个小组的学生（四重交集）
# 2. 找出参加了书法组，但既没有参加绘画组也没有参加音乐组的学生
# 3. 使用集合推导式找出参加了书法组，但没有参加体育组的学生
# 4. 求出所有参赛学生名单（四组并集），并统计总人数
# 5. 统计每位学生在四个小组中总共出现的次数, 并输出(形式为: xxx 参加了 xxx 个小组)


# 书法组
calligraphy_set = {"王林", "曾牛", "天运子", "韩立", "厉飞雨", "紫灵", "徐立国"}
# 绘画组
painting_set    = {"张铁", "王林", "曾牛", "王蝉", "韩立", "厉飞雨", "云露", "李化元"}
# 音乐组
music_set       = {"许木", "红蝶", "韩立", "天运子", "厉飞雨", "曾牛", "虎咆"}
# 体育组
sports_set      = {"遁天", "天运子", "韩立", "姜老道", "紫灵", "云露", "虎咆"}

intersection_set = calligraphy_set & painting_set & music_set & sports_set
print(f" intersection_set: {intersection_set}")

answer2 = calligraphy_set - music_set - painting_set
print(f" answer2: {answer2}")

answer3 = [e for e in calligraphy_set if e not in sports_set]
print(f" answer3: {answer3}")

answer4 = calligraphy_set | painting_set | music_set | sports_set
print(f" answer4: {answer4}")

for i, e in enumerate(answer4) :
    dic = {"name": e, "group": []}
    if e in painting_set:
        dic["group"].insert(0, "绘画")

    if e in music_set:
        dic["group"].insert(0, "音乐")

    if e in sports_set:
        dic["group"].insert(0, "体育")
    print(f"{e} 参与了 {dic["group"]} {len(dic["group"])}个小组")

# all_members = [*calligraphy_set, *painting_set, *music_set, *sports_set]
# for e in all_members:
#     count = all_members.count(e)
#     print(f"   {e} 参加了 {count} 个小组")



# 【题目】
# 已知若干学生的课程选课数据：
# students = (
#     ("S001", "王林", {"语文", "数学", "英语", "历史"}),
#     ("S002", "李慕婉", {"数学", "物理"}),
#     ("S003", "司徒南", {"语文", "英语", "历史"}),
#     ("S004", "柳眉", {"数学", "英语", "物理"}),
#     ("S005", "周佚", {"语文", "数学", "化学", "历史"}),
#     ("S006", "清水仙君", {"语文", "数学", "AI", "日语"}),
#     ("S007", "红蝶", {"英语", "数学", "日语"}),
#     ("S008", "徐立国", {"语文", "英语", "历史"}),
#     ("S009", "许立国", {"语文", "历史", "AI"}),
#     ("S010", "藤化元", {"语文", "英语", "化学", "韩语"})
# )
# hot_courses = {"数学", "英语", "物理"}
#
# 请依次完成以下操作（不使用函数）：
# 1. 使用元组解包遍历所有学生，输出每个学生的学号、姓名和所选课程
# 2. 求出所有学生选过的全部课程集合 all_courses
# 3. 计算每个学生的总学分（每门课 3 学分）, 并输出(形式: "xxx 选修了 xxx 课程, 总学分 xxx 分")
# 4. 找出所选课程中至少包含 2 门热门课程的学生
# 5. 找出选了"数学"但没选"物理"的学生姓名

students = (
    ("S001", "王林", {"语文", "数学", "英语", "历史"}),
    ("S002", "李慕婉", {"数学", "物理"}),
    ("S003", "司徒南", {"语文", "英语", "历史"}),
    ("S004", "柳眉", {"数学", "英语", "物理"}),
    ("S005", "周佚", {"语文", "数学", "化学", "历史"}),
    ("S006", "清水仙君", {"语文", "数学", "AI", "日语"}),
    ("S007", "红蝶", {"英语", "数学", "日语"}),
    ("S008", "徐立国", {"语文", "英语", "历史"}),
    ("S009", "许立国", {"语文", "历史", "AI"}),
    ("S010", "藤化元", {"语文", "英语", "化学", "韩语"})
)
hot_courses = {"数学", "英语", "物理"}

print("*" * 20)

# # 1. 使用元组解包遍历所有学生，输出每个学生的学号、姓名和所选课程
# for sid, name, courses in students:
#     print(f"学号: {sid}, 姓名: {name}, 选修课程: {courses}")

all_courses = set()
for sid, name, courses in students:
    print(f"学号: {sid}, 姓名: {name}, 选修课程: {courses}")
    all_courses = all_courses | courses
print(f"all_courses: {all_courses}")

for sid, name, courses in students:
    print(f"{name}选修了 {", ".join(courses)} {len(courses)}课程, 总学分 {len(courses) * 3} 分 ")

stu_hot = [e for e in students if len(hot_courses & e[2]) >= 2]
print(f"stu_hot: {stu_hot}")

stu_5 = [e for e in students if "数学" in e[2] and "物理" not in e[2]]
print(f"stu_5: {stu_5}")
