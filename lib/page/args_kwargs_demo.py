def add_contact_new(
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
):
    """添加联系人"""
    print("\n【添加联系人】")
    name = name or input("请输入姓名：").strip()
    phone = phone or input("请输入手机号：").strip()
    email = email or input("请输入邮箱：").strip()
    print(",".join([name, phone, email]))

add_contact_new(name="九歌", phone="999999999999", email="jiuge@163.com")
add_contact_new()

