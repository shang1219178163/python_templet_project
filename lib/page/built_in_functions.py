
arr = [3, 1, 2, 4]
length = len(arr)
print(f"arr: {arr} length: {length}")

arrSorted = sorted(arr)
print(f"sorted: {arrSorted}")

arrReversed = list(reversed(arr))
print(f"reversed: {arrReversed}")

arr1 = list(map(lambda x: x * 2, arr))     # [2, 4, 6]
print(f"map: {arr1}")

arr2 = list(enumerate(arr))
print(f"enumerate: {arr2}  {type(arr2)}")

arr3 = list(filter(lambda x: x > 2, arr))
print(f"filter: {arr3}")


ar = ["d", "c", "b", "a"];
arr4 = list(zip(ar, arr))
print(f"zip: {arr4}")


arr5 = list(range(2, 10, 1))
print(f"range: {arr5}")


arr6 = arr5[slice(1, 7)]
print(f"slice: {arr6}")