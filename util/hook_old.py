# from datetime import datetime
# from functools import wraps
# from types import FunctionType
# from typing import Any, Callable
#
#
# def hook_old(
#     before: Callable[..., None] | None = None,
#     after: Callable[..., None] | None = None,
#     on_error: Callable[..., None] | None = None,
# ) -> Callable[..., Callable[..., Any]]:
#     """
#     添加面向切面编程（AOP）
#     :param before:
#     :param after:
#     :param on_error:
#     :return:
#     """
#     def decorator(func: FunctionType) -> Callable[..., Any]:
#         code = func.__code__
#         filename = code.co_filename.split("/")[-1]  # 函数定义所在文件
#         lineno = code.co_firstlineno  # 函数定义所在行号
#         func_name = code.co_name  # 函数名
#         # func_name = func.__name__  # 函数名
#         # //[log] [2025-03-27 10:13:00.727041][ERROR][ios][_MetaDataDemoState.onTest Line:164]:
#         extra =  [f"{filename.split(".")[0]}.{func_name}", f"Line:{lineno}"]
#
#         @wraps(func)
#         def wrapper(*args: Any, **kwargs: Any) -> Any:
#             if before:
#                 before(*args, extra = extra, **kwargs)
#             try:
#                 result = func(*args, **kwargs)
#             except Exception as e:
#                 if on_error:
#                     on_error(*args, extra = extra, **kwargs)   # 统一签名，异常信息自行闭包获取
#                 raise
#             if after:
#                 after(*args, extra = extra, result=result, **kwargs)
#             return result
#         return wrapper
#     return decorator
#
#
# def on_before(*args: Any, extra: list, **kwargs: Any) -> None:
#     date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#     print(f"[{date_str} before {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]")
#
# def on_after(*args: Any, extra: list, result: Any, **kwargs: Any) -> None:
#     date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#     print(f"[{date_str} after  {extra[0]}(args={args}, kwargs={kwargs}) {extra[1]}]: {result}")
#
#
# # 测试代码
# if __name__ == "__main__":
#
#     @hook_old(before=on_before, after=on_after)
#     def add(a: int, b: int) -> int:
#         return a + b
#
#     print(add(1, 2))
