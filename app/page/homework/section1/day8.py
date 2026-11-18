a = []
b = ()
b1 = (1)  # int
b2 = (1,)  # int
c = None

print([type(e) for e in [a, b, b1, b2, c]])

if a:
    print("a")
else:
    print("a 为空")

if b:
    print("b")
else:
    print("b 为空")

if c:
    print("c")
else:
    print("c 为空")
