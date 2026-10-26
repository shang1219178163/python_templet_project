from util.dlog import DLog

arr = list(range(10))
DLog.d(f"arr: {type(arr)} {arr}")

val = pow(2, 3)
DLog.d(f"val: {type(val)} {val}")

v1 = 100
v2 = 200
v3 = 300

(c, b, a) = (v1, v2, v3)
DLog.d(f"a: {a}, b: {b}, c: {c}")


v1, v2 = v2, v1
DLog.d(f"v1: {v1}, v2: {v2}")

DLog.d(f"pre a: {a}, b: {b}, c: {c}")
c,a,b = a,b,c
DLog.d(f"a: {a}, b: {b}, c: {c}")