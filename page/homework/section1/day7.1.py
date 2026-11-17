"""
>> 通讯录管理系统

1.需求说明：开发一个简单的通讯录管理系统，使用 TXT 文件存储联系人信息

2.数据存储格式（contacts.txt）：
张三|13800138001|zhangsan@example.com
李四|13800138002|lisi@example.com
王五|13800138003|wangwu@example.com

3.功能要求：
    添加联系人：输入姓名、电话、邮箱，追加到文件末尾
    查看所有联系人：读取并格式化展示所有联系人
    搜索联系人：根据姓名搜索联系人
    使用 with 上下文管理器操作文件
"""

from pathlib import Path
from util.file_manager import FileManager

path = Path("contacts.txt")

def add_contact(**kwargs):
    """添加联系人"""
    print("\n【添加联系人】")
    name = kwargs.get("name") or input("请输入姓名：").strip()
    email = kwargs.get("email") or input("请输入邮箱：").strip()
    phone = kwargs.get("phone") or input("请输入11位手机号：").strip()

    # 验证手机号是否为11位数字 -> isdigit() 可判定是否为数字
    # 以追加模式(模式不要用 "w", 用 "a")写入 contacts.txt，格式：姓名|电话|邮箱
    if phone.isdigit() is False or len(phone) != 11:
        while True:
            phone = input("请输入11位手机号：").strip()               
            print(f"{phone} 长度 {len(phone)}")
            if phone.isdigit() and len(phone) == 11:
                new_line = "|".join([name, phone, email]) + "\n"
                success = FileManager.write(path=path, new_line=new_line)
                print(f"{"添加成功！" if success else "添加失败！"}")
                break


def show_all_contacts():
    """查看所有联系人"""
    print("\n【所有联系人】")

    # 读取 contacts.txt 文件
    # 格式化展示：姓名、电话、邮箱
    # 如果文件不存在或为空，提示"暂无联系人"
    items = FileManager.read(path=path)
    print(items)

def search_contact():
    """搜索联系人"""
    print("\n【搜索联系人】")
    keyword = input("请输入要搜索的姓名：").strip()

    items = FileManager.search(path=path, key= keyword, cb = match_name)
    print(items)


def del_contact():
    """删除联系人"""
    print("\n【删除联系人】")
    keyword = input("请输入要删除的姓名：").strip()

    # FileManager.delete(path=path, keyword = keyword, cb=match_name)
    success = FileManager.delete(path=path, key = keyword, cb=lambda k, items: [e for e in items if k in e])
    print(f"del_contact {"成功！" if success else "失败！"}")

def update_contact():
    print("\n【更新】")
    keyword = input("请输入更新的姓名：").strip()
    email = input("请输入修改邮箱：").strip()
    phone = input("请输入修改(11位)手机号：").strip()

    def update_match(key: str, targets: list[str])-> list[str]:
        new_line = "|".join([key, phone, email]) + "\n"
        return [ new_line ]

    success = FileManager.update(path=path, key=keyword, search_cb=match_name, update_cb=update_match)
    print(f"update_contact {"成功！" if success else "失败！"}")


# 匹配姓名
def match_name(keyword:str, items: list[str]) -> list[str]:
    """匹配姓名"""
    res = [e for e in items if keyword in e.split("|")[0]]
    return res

def run():
    while True:
        print("===== 通讯录管理系统 =====")
        tips = [
            "1.添加",
            "2.查看",
            "3.搜索",
            "4.更新",
            "5.删除",
            "6.退出"
        ]
        print("\t".join(tips))

        choice = input("请选择操作(1-6): ").strip()
        match choice:
            case "1":
                add_contact()
            case "2":
                show_all_contacts()
            case "3":
                search_contact()
            case "4":
                update_contact()
            case "5":
                del_contact()
            case "6":
                print("再见！")
                break
            case _:
                print("无效选项！")


if __name__ == "__main__":
    run()
#

