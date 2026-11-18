import functools
import time


def exec_timer(func):
    """计算函数执行时间的装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result

    return wrapper


@exec_timer
def slow_function():
    time.sleep(1)
    return "Done"


print(slow_function())  # slow_function took 1.0012s\nDone
