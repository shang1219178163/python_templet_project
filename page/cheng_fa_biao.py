

def cheng_fa_biao(count: int = 9):
    # 乘法表
    for i in range(1, count + 1):
        for j in range(1, i + 1):
            desc = f"{i} x {j} = {i * j}"
            endStr = "\t\t" if (i >= 10 or j >= 10) else "\t"
            print(desc, end=endStr)
        print()


def cheng_fa_biao_new(count: int = 9):
    for i in range(1, count + 1):
        for j in range(1, i + 1):
            lg = len(f"{i * j}")
            muti_pad = (3 - lg + 1) * " "
            endStr = "\n" if i == j else ""
            print(f"{i} * {j} = {i * j}{muti_pad}", end=endStr)
