from collections.abc import Callable
from pathlib import Path


class FileManagerNew:

    @staticmethod
    def write(path: Path, new_line: str) -> bool:
        """写入"""
        try:
            with path.open("a+", encoding="utf-8") as f:
                lines = f.readlines()
                row = new_line
                if row in lines:
                    print(f"数据已存在 {row}")
                    return False
                f.write(row)
                print("添加成功！")
                return True

        except OSError as err:
            print(f"存储失败 {err}")

        return False

    @staticmethod
    def read(path: Path) -> list[str]:
        """查看所有"""
        # print("\n【查看所有】")
        # 如果文件不存在或为空，提示"暂无"
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # print("".join(lines))
                return lines

        except OSError as err:
            print(f"存储失败 {err}")

        return []

    @staticmethod
    def search(path: Path, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> list[str]:
        """搜索"""
        # print("\n【搜索】")
        # 读取文件，查找包含关键字的行
        # 展示匹配结果
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                return targets

        except OSError as err:
            print(f"搜索失败 {err}")

        return []

    @staticmethod
    def delete(path: Path, key: str, cb: Callable[[str, list[str]], list[str]] | None = None) -> bool:
        """删除"""
        # print("\n【删除】")

        # 删除 = 全量读到内存 → 内存里删 → 用 "w" 模式整体写回
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                targets = cb(key, lines) if cb else [e for e in lines if key in e]
                if not targets:
                    print(f"未找到包含「{key}")
                    return False

                # print(f"targets:{targets}")
                new_lines = [x for x in lines if x != targets[0]]  # 只删第一条匹配
                # print(f"lines:{new_lines}")
                with path.open("w", encoding="utf-8") as fin:
                    fin.writelines(new_lines)
                print("删除成功!")
                return True

        except FileNotFoundError as e:
            print(f"暂无 {e}")
            return False
        except OSError as err:
            print(f"失败 {err}")
            return False

    @staticmethod
    def update(path: Path,
               key: str,
               search_cb: Callable[[str, list[str]], list[str]] | None = None,
               update_cb: Callable[[str, list[str]], list[str]] | None = None,
               ) -> bool:
        """更新：定位第一条匹配行，用 update_cb 生成的新行替换后整体写回"""
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

                targets = search_cb(key, lines) if search_cb else [e for e in lines if key in e]
                if not targets:
                    print(f"未找到包含「{key}」的内容")
                    return False

                idx = lines.index(targets[0])
                # update_cb 返回新行列表（一行换多行也支持）；未传回调则原样保留
                new_row = update_cb(key, targets) if update_cb else [targets[0]]
                lines[idx:idx + 1] = new_row

            with path.open("w", encoding="utf-8") as f:
                f.writelines(lines)
                print("更新成功!")
                return True

        except FileNotFoundError as e:
            print(f"暂无 {e}")
            return False
        except OSError as err:
            print(f"更新失败 {err}")
            return False
