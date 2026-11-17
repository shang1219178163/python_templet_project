import json
from pathlib import Path

import streamlit as st

from lib.util.dlog import DLog

# 本文件在 lib/page/io/ 下，往上三级是 lib 目录，assets 位于 lib/assets
resource_root = Path(__file__).resolve().parents[2]
target_path = f"{resource_root}/assets/txt/kuan_rong.txt"
DLog.d(target_path)
# target_path.parent.mkdir(parents=True, exist_ok=True)

# 写入文件内容
with open(target_path, "w", encoding="utf-8") as f:
    f.writelines(
        """
《宽容》序言是荷裔美国作家亨德里克·威廉·房龙为其1925年出版的著作《宽容》所写的序言。它并非通常的致谢或说明，而是一则独立的寓言故事，以散文诗般的语言，浓缩表达了全书的核心思想：**倡导思想自由，主张对异见宽容，谴责愚昧与专制对真理的扼杀**。

### 📖 寓言情节梗概

故事发生在一个与世隔绝的“无知山谷”。这里的人们世代遵循古老律法，在守旧老人的统治下过着封闭而“幸福”的生活。山谷外的一切都被视为禁忌。

一位敢于探索的“漫游者”冲破禁忌，发现了山外繁荣的新世界。他返回山谷，试图说服村民跟随他离开，却因“亵渎”祖先智慧而被守旧老人判处死刑，最终被村民用石块砸死。

不久，山谷遭遇特大干旱，生存危机迫使幸存者反抗律法，沿着漫游者留下的路标成功找到了新家园。此时人们才幡然醒悟，先驱者是对的，而他们却亲手杀死了他。故事结尾，人们为这位“首先向未知世界和恐怖挑战的人”立碑纪念，并希望这样的悲剧将来不再发生。

### 🔍 核心象征与寓意

*   **无知山谷**：象征着封闭、保守、拒绝新知的旧秩序与旧观念。
*   **守旧老人**：象征着固守传统、以僵化律法压制新思想的权威势力。他们并非天生残忍，但为了维护律法而变得冷酷。
*   **漫游者（先驱者）**：象征着敢于怀疑、探索真理并为之献身的革新者。他的悲剧揭示了先驱者往往需要付出生命的代价，其价值才可能被后世认可。
*   **村民**：象征着受蒙蔽的普通大众。他们起初盲从权威、参与迫害，只有在现实绝境中才被迫醒悟。这揭示了接受真理往往需要一个痛苦而漫长的过程。

房龙通过这个故事揭示了他对“不宽容”根源的理解：**恐惧**。守旧老人和村民对未知的恐惧，使他们本能地排斥和迫害提出异见的人。这篇序言也因此成为对一切思想禁锢的深刻警示。
"""
)


# 读取文件内容
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()
    DLog.d(f"content: {content}")



user = {
    "name": "张三",
    "age": 18,
    "gender": "男",
    "hobbies": ["阅读", "编程", "旅行"],
    "address": {
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "street": "科技园路"
    }
}

with open(f"{resource_root}/assets/json/user.json", "w", encoding="utf-8") as f:
    json.dump(user, f, ensure_ascii=False, indent=4)