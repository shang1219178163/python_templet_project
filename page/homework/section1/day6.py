


user = {"name": "张三"}
extra = {"age": 18, "city": "北京"}

result = {**user, **extra}
# {'name': '张三', 'age': 18, 'city': '北京'}

result_keys = {*user, *extra}
# {'name', 'age', 'city'}

print(result)
print(result_keys)


s1 = "hellow-python"
print(s1[-2])


li = [1, 2,3,4,5, 6]
li.remove(3)
print(f"li: {li}")

del li[3]
print(f"li: {li}")

s1_sp = s1.split(" ")
print(f"split:{type(s1_sp)}, {s1_sp}, {"_".join(s1_sp)}")

