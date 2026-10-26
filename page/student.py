import json
import sys
from pathlib import Path
from typing import Any

# 本文件在 page/ 下，上一级才是项目根目录
project_root = Path(__file__).resolve().parent.parent
project_root_path = str(project_root)
if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

from model.student_model import StudentModel
from util.dlog import DLog

# 分数json文件路径
SCORE_PATH = project_root / "assets" / "json" / "student_score.json"


def load_students(path: Path) -> list[StudentModel]:
    """读取成绩 JSON，并解码为学生模型列表。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    # print(f"data: {type(data)}")
    return [StudentModel.from_dict(item) for item in data]


models = load_students(SCORE_PATH)

#
# for e in models:
#     DLog.d(f"{e.to_dict()}, {e.total_score}, {e.average_score}")


chineseScores = list(map(lambda e1: (e1.name, e1.chinese), models))
DLog.d(f"chineseScores {chineseScores}")

# chineseScores = [(e.name, e.chinese) for e in models]
# DLog.d(f"chineseScores: {chineseScores}")


englishScores = [(e.name, e.english) for e in models]
DLog.d(f"englishScores: {englishScores}")

mathScores = [(e.name, e.math) for e in models]
DLog.d(f"mathScores: {mathScores}")


chineseSorted = sorted(models, key=lambda e: e.chinese)
englishSorted = sorted(models, key=lambda e: e.english)
mathSorted = sorted(models, key=lambda e: e.math)
# print(f'{chineseScores}')
# print(f'{englishScores}')
# print(f'{mathScores}')

def log_student(m: StudentModel, k: str) -> tuple[str, Any]:
    return m.name, m.to_dict()[k]

print(f"chineseSorted: {log_student(chineseSorted[0], "chinese")}, {log_student(chineseSorted[-1], "chinese")}")
print(f"englishSorted: {log_student(englishSorted[0], "english")}, {log_student(englishSorted[-1], "english")}")
print(f"mathSorted: {log_student(mathSorted[0], "math")}, {log_student(mathSorted[-1], "math")}")





