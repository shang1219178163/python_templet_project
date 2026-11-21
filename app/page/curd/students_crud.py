"""
    案例:
    开发一个学生管理系统，实现信息的添加、修改、删除和查询功能。
    系统使用嵌套字典结构存储数据，通过控制台菜单与用户交互。
    具体功能如下：
        1. 添加学生：用户根据提示录入名称、以及语文/数学/英语成绩，保存该信息。
        2. 修改学生：要求用户输入要修改的学生名称，然后再提示输入各科成绩，输入完成后修改该信息。
        3. 删除学生：要求用户输入要删除的学生名称，根据名称删除学生。
        4. 查询学生：将学生信息逐条展示出来。
        5. 退出系统

    结构: student_dic = {"张三": {"chinese": 90, "math": 85, "english": 88}}
"""

from collections.abc import Mapping

from app.util.console_crud import ConsoleCrud, CrudField, CrudRow


def format_student(name: str, row: CrudRow) -> str:
    """单条展示：姓名 + 各科成绩 + 总分"""
    total_score = sum(row.values())
    avg_score = round(total_score / len(row.values()))

    keys = sorted(row.keys())
    items = ", ".join([f"{e} {row[e]:g}" for e in keys])
    return f"{name}: {items}, 总分 {sum(row.values()):g}, 平均分{avg_score}"


def summarize_students(data: Mapping[str, CrudRow]) -> str:
    """汇总行：人数 + 平均总分（空数据时 show 不会调用到这里）"""
    avg = sum(sum(row.values()) for row in data.values()) / len(data)
    # print(f"summarize_students_{type(data.values())}_{data.values()}")
    return f"共 {len(data)} 名学生，平均总分 {avg:g}"


student_crud = ConsoleCrud(
    title="学生管理系统",
    entity="学生",
    key_prompt="学生姓名：",
    fields={
        "chinese": CrudField("语文成绩：", ConsoleCrud.read_float),
        "math": CrudField("数学成绩：", ConsoleCrud.read_float),
        "english": CrudField("英语成绩：", ConsoleCrud.read_float),
    },
    format_row=format_student,
    summarize=summarize_students,
    empty_hint="暂无学生记录",
)

if __name__ == "__main__":
    student_crud.batch_import({
        "张三": {"chinese": 90.5, "math": 85, "english": 88},
        "李四": {"chinese": 78.7, "math": 92, "english": 80},
        "王五": {"chinese": 88.9, "math": 76, "english": 95},
    })
    student_crud.run()
