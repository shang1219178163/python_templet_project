
from lib.model import book_library_model

library = book_library_model.BookLibraryModel()


# 初始化图书馆模型
books = library.load_books(count=10)
book_titles = [f"{books.index(book)},{book.title},{book.isbn}" for book in books]
print(f"图书馆藏书列表:\n{'\n'.join(book_titles)},共{len(books)}本")

isbn = "9787030000088"

# 获取模型列表中第一个目标模型
target = next((e for e in books if e.isbn == isbn), None)
print(f"查找第一个符合条件的模型 target: {target.title}, {target.isbn}" if target else "target: None")

# 获取模型列表中第一个目标模型的索引
idx = next((i for i, e in enumerate(books) if e.isbn == isbn), -1)
print(f"查找第一个符合条件的模型索引 idx: {idx}, {books[idx].title}" if idx != -1 else "idx: -1")

#拆分写法
indices = (i for i, e in enumerate(books) if e.isbn == isbn)
idxNew = next(indices, -1)

print(f"查找第一个符合条件的模型索引 idxNew: {idxNew}, idx == idxNew: {idx == idxNew}")

# 获取模型列表中所有符合条件的模型列表
results = [(i, e) for i, e in enumerate(books) if e.isbn == isbn]
print(f"查找所有符合条件的模型 results: {results}, {type(results)}")


# 快速初始化数组
squares = (n ** 2 for n in range(5))

print(next(squares))  # 0
print(next(squares))  # 1
print(list(squares))  # [4, 9, 16]

array = [n + 1 for n in range(5)]
print(array)  # [0, 1, 2, 3, 4]