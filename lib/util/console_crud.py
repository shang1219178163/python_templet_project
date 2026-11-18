"""控制台版字典增删改查的通用组件。

购物车、学生管理等 DEMO 都是同一套模式：
菜单循环 + 嵌套字典 ``{名称: {字段: 值, ...}}`` 的增、删、改、查。
本模块把这套流程收敛为一个可配置的类，各 DEMO 只声明标题、字段与展示格式。
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

type Row = dict[str, Any]
type Formatter = Callable[[str, Row], str]
type Summary = Callable[[Mapping[str, Row]], str | None]


@dataclass(slots=True, frozen=True)
class Field:
    """一个待录入字段：提示语 + 读取函数（如 ``ConsoleCRUD.read_float``）。"""

    prompt: str
    reader: Callable[[str], Any]


class ConsoleCRUD:
    """基于嵌套字典的控制台增删改查组件。

    数据结构约定：``{名称: {字段名: 值, ...}}``，名称即字典的 key。
    """

    menu_template = """
####################### {title} ########################
#        1.添加  2.修改  3.删除  4.查询  5.退出            #
#########################################################
"""

    def __init__(
            self,
            *,
            title: str,
            entity: str,
            fields: Mapping[str, Field],
            name_prompt: str | None = None,
            format_row: Formatter | None = None,
            summarize: Summary | None = None,
            empty_hint: str | None = None,
            data: dict[str, Row] | None = None,
    ) -> None:
        """
        :param title: 菜单标题，如「购物车系统」
        :param entity: 条目名称，用于拼接提示语，如「商品」「学生」
        :param fields: 字段名 -> Field，添加/修改时按顺序录入
        :param name_prompt: 录入名称时的提示语，默认「{entity}名称：」
        :param format_row: 单条展示格式，默认「名称: {字典}」
        :param summarize: 查询末尾的汇总行，返回 None 或空串则不打印
        :param empty_hint: 查询为空时的提示，默认「暂无{entity}记录」
        :param data: 外部传入的数据字典，便于复用已有数据
        """
        self.title = title
        self.entity = entity
        self.fields = dict(fields)
        self.name_prompt = name_prompt or f"{entity}名称："
        self.format_row = format_row or _default_format_row
        self.summarize = summarize
        self.empty_hint = empty_hint or f"暂无{entity}记录"
        self.data: dict[str, Row] = data if data is not None else {}

    # ---------------- 输入 ----------------

    @staticmethod
    def read_str(tips: str) -> str:
        """读取字符串：去首尾空格后返回。"""
        return input(tips).strip()

    @staticmethod
    def read_float(tips: str) -> float:
        """读取价格，非法时要求重新输入"""
        while True:
            price = float(input(tips).strip())
            if price is not None and price > 0:
                return price
            print("必须是非负数字，请重新输入")

    @staticmethod
    def read_int(tips: str) -> int:
        """读取数量，非法时要求重新输入"""
        while True:
            num = int(input(tips).strip())
            if num is not None and num > 0:
                return num
            print("必须是非负整数，请重新输入")

    # ---------------- 增删改查 ----------------

    def add(self) -> None:
        """添加：名称已存在时拒绝，避免覆盖原有数据"""
        name = self.read_str(self.name_prompt)
        if name in self.data:
            print(f"{self.entity}已存在，请执行修改操作")
            return
        self.data[name] = self._input_row()
        print(f"添加成功：{name}")

    def update(self) -> None:
        """修改：只允许修改已存在的"""
        name = self.read_str(self.name_prompt)
        if name not in self.data:
            print(f"{self.entity}不存在，请执行新增操作")
            return
        self.data[name] = self._input_row()
        print(f"修改成功：{name}")

    def delete(self) -> None:
        """删除：先判断存在，再按 key 删除"""
        name = self.read_str(self.name_prompt)
        if name not in self.data:
            print(f"{self.entity}不存在")
            return
        del self.data[name]
        print(f"删除成功：{name}")

    def batch_import(
            self,
            rows: Mapping[str, Row] | Iterable[tuple[str, Row]],
            *,
            overwrite: bool = False,
            validate: bool = True,
    ) -> int:
        """批量导入：把多条记录一次性写入。

        :param rows: ``{名称: 字段字典}`` 或 ``[(名称, 字段字典), ...]``
        :param overwrite: 名称已存在时 True 覆盖、False 跳过
        :param validate: 是否校验字段与 ``self.fields`` 一致，缺字段的记录会被跳过
        :return: 实际写入的条数
        """
        items = rows.items() if isinstance(rows, Mapping) else rows
        imported = skipped = invalid = 0
        for name, row in items:
            if validate and self.fields and not self.fields.keys() <= row.keys():
                missing = ", ".join(self.fields.keys() - row.keys())
                print(f"跳过 {name}：缺少字段 {missing}")
                invalid += 1
                continue
            if name in self.data and not overwrite:
                skipped += 1
                continue
            self.data[name] = dict(row)
            imported += 1
        print(f"批量导入完成：成功 {imported} 条，跳过 {skipped} 条，字段不符 {invalid} 条")
        return imported

    def show(self) -> None:
        """查询：逐条按 format_row 展示，末尾追加 summarize 汇总行"""
        if not self.data:
            print(self.empty_hint)
            return
        for name, row in self.data.items():
            print(self.format_row(name, row))
        if self.summarize is not None:
            line = self.summarize(self.data)
            if line:
                print(line)

    def run(self) -> None:
        """主循环：打印菜单，用模式匹配分发操作，选 5 退出"""
        while True:
            print(self.menu_template.format(title=self.title))
            oper = input("请输入对应操作编号（1-5）:").strip()
            match oper:
                case "1":
                    self.add()
                case "2":
                    self.update()
                case "3":
                    self.delete()
                case "4":
                    self.show()
                case "5":
                    print("退出成功，欢迎下次使用！")
                    break
                case _:
                    print("不支持该操作！")

    def _input_row(self) -> Row:
        """按 field 声明顺序逐个读取，组装成一行数据"""
        return {key: field.reader(field.prompt) for key, field in self.fields.items()}


def _default_format_row(name: str, row: Row) -> str:
    return f"{name}: {row}"
