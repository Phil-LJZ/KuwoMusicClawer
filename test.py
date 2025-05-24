class Parent(object):
    """测试类"""

    def __init__(self) -> None:
        print(f"Parent 类已被创建，内存地址{id(self)}")

if __name__ == "__main__":
    p = Parent()
    