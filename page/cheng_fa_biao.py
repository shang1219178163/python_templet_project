
# 乘法表
for i in range(1, 21):
    for j in range(1, i + 1):
        desc = f"{i} x {j} = {i * j}"
        endStr = "\t\t" if (i >= 10 or j >= 10) else "\t"
        print(desc, end=endStr)
    print()
