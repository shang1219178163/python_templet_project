from pathlib import Path
from typing import Callable


class FileManager:
    path: Path
    """文件路径"""

    def __init__(self, path: Path):
        self.path = path

    def write(self, new_line: str) -> bool:
        """写入"""
        try:
            all_lines = self.read()
            if new_line in all_lines:
                raise OSError(f"数据已存在: {new_line}")

            with self.path.open("a+", encoding="utf-8") as f:
                f.write(new_line)
                # print("添加成功！")
                return True

        except OSError as err:
            print(f"写入失败, {err}")

        return False

    def read(self) -> list[str]:
        """查看所有"""
        # print("\n【查看所有】")
        # 如果文件不存在或为空，提示"暂无"
        try:
            with self.path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # print("".join(lines))
                return lines

        except OSError as err:
            print(f"读取失败 {err}")

        return []

    def search(self, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> list[str]:
        """搜索"""
        # print("\n【搜索】")
        # 读取文件，查找包含关键字的行
        # 展示匹配结果
        try:
            with self.path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                return targets

        except OSError as err:
            print(f"查询失败 {err}")

        return []

    def delete(self, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> bool:
        """删除"""
        # print("\n【删除】")

        # 删除 = 全量读到内存 → 内存里删 → 用 "w" 模式整体写回
        try:
            with self.path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                if not targets:
                    raise OSError(f"未找到包含「{key}")

                # print(f"targets:{targets}")
                new_lines = [x for x in lines if x != targets[0]]  # 只删第一条匹配
                # print(f"lines:{new_lines}")
                with self.path.open("w", encoding="utf-8") as fin:
                    fin.writelines(new_lines)
                return True

        except FileNotFoundError as e:
            print(f"暂无 {e}")
            return False
        except OSError as err:
            print(f"失败 {err}")
            return False

    def update(self,
               key: str,
               search_cb: Callable[[str, list[str]], list[str]] | None = None,
               update_cb: Callable[[str, list[str]], list[str]] | None = None,
               ) -> bool:
        """更新：定位第一条匹配行，用 update_cb 生成的新行替换后整体写回"""
        try:
            with self.path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

                targets = search_cb(key, lines) if search_cb else [e for e in lines if key in e]
                if not targets:
                    raise OSError(f"未找到包含「{key}」的内容")

                idx = lines.index(targets[0])
                # update_cb 返回新行列表（一行换多行也支持）；未传回调则原样保留
                new_row = update_cb(key, targets) if update_cb else [targets[0]]
                lines[idx:idx + 1] = new_row

            with self.path.open("w", encoding="utf-8") as f:
                f.writelines(lines)
                return True

        except FileNotFoundError as e:
            print(f"暂无 {e}")
            return False
        except OSError as err:
            print(f"更新失败 {err}")
            return False
