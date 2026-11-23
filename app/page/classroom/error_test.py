from util.dlog import DLog as print


def test() -> None:
    try:
        print("----")
        dic = {}
        a = dic.get("a")
        b = dic["b"]
        print(f"a: {a}, b: {b}")
        raise ValueError("自定义错误")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        print("----")


def test2() -> None:
    dic = {}
    b = dic.get("b")
    print(b)

    b1 = dic["b"]
    print(b1)


if __name__ == "__main__":
    test()
    # test2()
