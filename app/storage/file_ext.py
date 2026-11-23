import json
from typing import Any, Callable


class FileExt:

    @classmethod
    def write_json(cls, obj: Any, file: str, to_dict: Callable[[Any], Any] | None = None, ) -> None:
        """写 JSON：自定义对象交给 to_dict() 转换"""
        with open(file, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4, default=to_dict)

    @classmethod
    def read_json(cls, file: str, ) -> Any:
        """读取JSON"""
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
