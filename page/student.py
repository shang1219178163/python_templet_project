import json
import sys
from pathlib import Path

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

# 打印最低分和最高分对应的姓名与成绩
def log_student(m: list[StudentModel], k: str) -> None:
    """按字段 k 从小到大排序，打印最低分和最高分对应的姓名与成绩。"""
    sorted_models = sorted(m, key=lambda e: e.to_dict()[k])
    lowest = sorted_models[0]
    highest = sorted_models[-1]
    print(
        f"{k}: min=({lowest.name}, {lowest.to_dict()[k]}), "
        f"max=({highest.name}, {highest.to_dict()[k]})"
    )

log_student(models, "chinese")
log_student(models, "english")
log_student(models, "math")

# 优秀学生
excellence_students = list(filter(lambda e: e.average_score >= 90, models))
excellence_student_names = list(map(lambda e: e.name, excellence_students))
DLog.d(f"excellence_student_names: {excellence_student_names}")