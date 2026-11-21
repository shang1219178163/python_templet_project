from mixins.repr_mixin import ReprMixin
from page.car_test import Car


class Car(ReprMixin):

    def __init__(self, name: str, price: float, brand: str, owner: str) -> None:
        self.name = name
        self.price = price
        self.brand = brand
        self.__owner = owner

    def getOwner(self):
        """Getter"""
        # print(f"调用owner getter {self.__owner}")
        return self.__owner

    @property
    def owner(self):
        """Getter"""
        # print(f"调用owner getter {self.__owner}")
        return self.__owner

    @owner.setter
    def owner(self, value: str):
        """Setter"""
        self.__owner = value
        # print(f"调用owner setter {self.__owner}")

    #
    # def __running(self):
    #     print("car is running!")

    @staticmethod
    def count():
        print("count")


class FullCar(Car):
    def __init__(self, name: str, price: float, brand: str, owner: str, tax_rate: float) -> None:
        Car.__init__(self, name, price, brand, owner)
        self.tax_rate = tax_rate

    def start(self):
        cls_name = self.__class__.__name__
        print(f"{type(self)}油车启动")


class ElectricCar(Car):
    def __init__(self, name: str, price: float, brand: str, owner: str, tax_rate: float) -> None:
        Car.__init__(self, name, price, brand, owner)
        self.tax_rate = tax_rate

    def start(self):
        cls_name = self.__class__.__name__
        print(f"{type(self)}电车启动")


car = FullCar(name="bmw3", price=250000, brand="bmw", owner="王林", tax_rate=0.1)
ecar = ElectricCar(name="bmw5", price=250000, brand="bmw", owner="王林", tax_rate=0.15)

# print(car.owner)
# print(car._Car__owner)
# car._Car__running()
#
car.owner = "任我行"
print(f"car.owner: {car.owner}")

print(f"{car}")

car.start()
ecar.start()

car.count()
