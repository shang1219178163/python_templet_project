class Car:
    def __init__(self, *, name: str, price: float, brand: str) -> None:
        self.name = name
        self.price = price
        self.brand = brand

    def running(self):
        print(f"{self.name} is running!")

    def calc(self, count: int):
        return self.price * count

    @property
    def wheel(self):
        return self.price * 2

    def __repr__(self) -> str:
        return f"Car({self.name}, {self.price}, {self.brand})"

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Car) and self.price == o.price

    def __lt__(self, o: object) -> bool:
        return isinstance(o, Car) and self.price < o.price

    def __le__(self, o: object) -> bool:
        return isinstance(o, Car) and self.price <= o.price

    def __ge__(self, o):
        return isinstance(o, Car) and self.price >= o.price

    def __gt__(self, o: object) -> bool:
        return isinstance(o, Car) and self.price > o.price


car = Car(name="bmw3", price=300000, brand="bmw")
car2 = Car(name="bmw3", price=500000, brand="bmw")

print(car.__dict__)

car.running()
print(car.calc(5))

print([
    car >= car2,
    car <= car2,
    car == car2,
])

print(car.wheel)
Car.wheel = 48
print(Car.wheel)
