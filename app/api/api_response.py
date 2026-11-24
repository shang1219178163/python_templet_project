# from pydantic import BaseModel
from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    """接口返回基类模型"""
    code: int
    message: str
    data: T | None
