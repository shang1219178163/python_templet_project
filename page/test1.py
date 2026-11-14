from datetime import datetime

dateStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
print(f"{dateStr} Hello, World!")


l = ["白日依山尽", "黄河入海流", "欲穷千里目", "更上一层楼"]

for i, e in enumerate(l):
    if e == l[0]:
        print(f"{datetime.now()} # ######## #")
        print(f"{datetime.now()} # {e} #")
    elif e == l[-1]:
        print(f"{datetime.now()} # {e} #")
        print(f"{datetime.now()} # ######## #")
    else:
        print(f"{datetime.now()} # {e} #")


print(int(True))
print(int(False))
print(None, type(None), None is None)