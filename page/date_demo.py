"""字符串时间 / datetime / 时间戳 三种时间表示互转示例。

不封装函数，直接演示 4 个底层 API：
    datetime.strptime(字符串, 格式)   → datetime
    datetime.strftime(格式)           → 字符串
    datetime.timestamp()              → 秒数
    datetime.fromtimestamp(秒, tz)    → datetime
"""

from datetime import datetime, timezone

fmt = "%Y-%m-%d %H:%M:%S"
date_str = "2026-11-16 10:57:00"

# 1) 字符串 → datetime
dt = datetime.strptime(date_str, fmt)
print(f"字符串 → datetime: {dt!r}")

# 2) datetime → 字符串
print(f"datetime → 字符串: {dt.strftime(fmt)}")

# 3) datetime → 时间戳（秒）
ts = dt.timestamp()
print(f"datetime → 时间戳: {ts}")

# 4) 时间戳 → datetime（tz=None 按本地时区；传 timezone.utc 得到 UTC 时间）
print(f"时间戳 → datetime（本地）: {datetime.fromtimestamp(ts)}")
print(f"时间戳 → datetime（UTC）: {datetime.fromtimestamp(ts, tz=timezone.utc)}")

# 5) 字符串 → 时间戳（先 strptime 再 timestamp）
print(f"字符串 → 时间戳: {datetime.strptime(date_str, fmt).timestamp()}")

# 6) 时间戳 → 字符串（先 fromtimestamp 再 strftime）
print(f"时间戳 → 字符串（本地）: {datetime.fromtimestamp(ts).strftime(fmt)}")
print(f"时间戳 → 字符串（UTC）: {datetime.fromtimestamp(ts, tz=timezone.utc).strftime(fmt)}")

# 7) 往返互转验证：本地时区下应原样还原
assert datetime.strptime(dt.strftime(fmt), fmt) == dt
assert datetime.fromtimestamp(dt.timestamp()) == dt
assert datetime.fromtimestamp(datetime.strptime(date_str, fmt).timestamp()).strftime(fmt) == date_str
print("互转往返验证通过")

# 8) 格式串带 %z 才会保留时区，否则解析回来只剩 naive 时间
aware = datetime(2026, 11, 16, 2, 57, tzinfo=timezone.utc)
aware_text = aware.strftime("%Y-%m-%d %H:%M:%S%z")
print(f"带时区字符串: {aware_text}")
print(f"解析回来: {datetime.strptime(aware_text, '%Y-%m-%d %H:%M:%S%z')}")

# 9) ISO 8601 字符串可免写格式串（3.11+ 支持末尾 Z）
print(f"ISO 解析: {datetime.fromisoformat('2026-11-16T10:57:00')}")
print(f"ISO 带时区: {datetime.fromisoformat('2026-11-16T10:57:00+08:00')}")

# 10) 当前时间的三种形态
now = datetime.now(timezone.utc)
print(f"当前时间（UTC）: {now.strftime(fmt)}")
print(f"当前时间戳（秒）: {int(now.timestamp())}")
print(f"当前时间戳（毫秒）: {int(now.timestamp() * 1000)}")
