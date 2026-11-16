"""演示 enums.weekday_enum.WeekdayEnum 的各种取值方式。直接运行本文件即可看到全部结果。"""

import sys
from pathlib import Path
from typing import cast

# 本文件在 page/ 下，导入 enums 包需要先把项目根目录加入 sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from enums.weekday_enum import WeekdayEnum


def run_demo() -> None:
    """逐条打印常见的取值写法。"""
    print("== 1. 直接取成员 ==")
    print(WeekdayEnum.MON.name, WeekdayEnum.MON.value, WeekdayEnum.MON.desc)
    print("getattr:", getattr(WeekdayEnum, "FRI").desc)

    print("\n== 2. 按值取（内置，O(1)） ==")
    print(WeekdayEnum(3).name, WeekdayEnum(3).desc)
    print("非法值:")
    try:
        WeekdayEnum(8)
    except ValueError as exc:
        print("  ValueError:", exc)

    print("\n== 3. 按名字取 ==")
    print(WeekdayEnum["SUN"].desc)
    # noinspection PyProtectedMember
    sun = cast(WeekdayEnum, WeekdayEnum._member_map_["SUN"])
    print(sun.desc, "（_member_map_ 是内部字典，谨慎使用）")

    print("\n== 4. 遍历 ==")
    for item in WeekdayEnum:
        print(item.name, item.value, item.desc)

    print(f"type: {type(WeekdayEnum)}")

    day = int(input("请输入星期:"))
    print(f"{WeekdayEnum(day)}")

if __name__ == "__main__":
    run_demo()
