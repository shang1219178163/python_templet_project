from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar, cast

class FileManager:

    @staticmethod
    def write(path: Path, new_line: str)-> None:
        """写入"""
        try:
            with path.open("a+", encoding="utf-8") as f:
                lines = f.readlines()
                row = new_line
                if row in lines:
                    print(f"数据已存在 {row}")
                    return
                f.write(row)
                print("添加成功！")
        except OSError as err:
            print(f"存储失败 {err}")

    @staticmethod
    def show_all(path: Path) -> None:
        """查看所有"""
        # print("\n【查看所有】")
        # 如果文件不存在或为空，提示"暂无"
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                print("".join(lines))

        except OSError as err:
            print(f"存储失败 {err}")

    @staticmethod
    def search(path: Path, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> None:
        """搜索"""
        # print("\n【搜索】")
        # 读取文件，查找包含关键字的行
        # 展示匹配结果
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                print(targets)

        except OSError as err:
            print(f"存储失败 {err}")

    @staticmethod
    def delete(path: Path, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> None:
        """删除"""
        # print("\n【删除】")

        # 删除 = 全量读到内存 → 内存里删 → 用 "w" 模式整体写回
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                if not targets:
                    print(f"未找到包含「{key}")
                    return

                # print(f"targets:{targets}")
                new_lines = [x for x in lines if x != targets[0]]  # 只删第一条匹配
                # print(f"lines:{new_lines}")
                with path.open("w", encoding="utf-8") as fin:
                    fin.writelines(new_lines)
                print("删除成功!")

        except FileNotFoundError as e:
            print(f"暂无 {e}")
            return
        except OSError as err:
            print(f"失败 {err}")
            return