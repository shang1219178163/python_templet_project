"""
员工工资计算系统
    需求说明: 某公司有三种类型的员工，基本工资相同，但奖金计算方式不同。使用抽象类规范工资计算方法。
    技术要求:
        创建抽象类 Employee
        属性：emp_id（工号）、name（姓名）、base_salary（基本工资，默认5000） ---> 参数设置默认值
        抽象方法：calculate_bonus()（计算奖金），子类必须实现
        普通方法：total_salary()（总工资 = 基本工资 + 奖金）
        普通方法：show_info()（展示员工信息）
    创建三个子类:
        Salesman（销售员）：奖金 = 销售额 × 提成比例（5%） ---> 扩充属性: 销售金额 sales_amount
        Manager（经理）：奖金固定为 3000
        Programmer（程序员）：奖金 = 完成项目数 × 500  -----> 扩充属性: 完成项目数 projects_completed
    测试程序:
        创建不同类型的员工
        计算并展示每个员工的总工资

测试代码:
# 测试代码
if __name__ == "__main__":
    employees = [
        Salesman("S001", "张三", 5000),
        Manager("M001", "李四"),
        Programmer("P001", "王五", 3)
    ]

    print("=" * 70)
    print("员工工资表")
    print("=" * 70)
    for emp in employees:
        emp.show_info()
    print("=" * 70)
"""

from abc import ABC, abstractmethod

from charset_normalizer.md import SuperWeirdWordPlugin


class Employee(ABC):

    def __init__(self, /, emp_id:str, name: str, base_salary: float):
        self.emp_id = emp_id
        self.name = name
        self.base_salary = base_salary

    @abstractmethod
    def calculate_bonus(self) -> float:
        """计算奖金"""
        pass

    def total_salary(self):
        """总工资 = 基本工资 + 奖金"""
        return self.base_salary + self.calculate_bonus()

    def show_info(self):
        """展示员工信息"""
        desc = f"工号：{self.emp_id} | 姓名：{self.name} | 基本工资：{self.base_salary} | 奖金：{self.calculate_bonus()} | 总工资：{self.total_salary()}"
        print(desc)


# Salesman（销售员）：奖金 = 销售额 × 提成比例（5%） ---> 扩充属性: 销售金额 sales_amount
class Salesman(Employee):
    sales_amount: float
    """销售金额"""

    def __init__(self, /, emp_id: str, name: str, base_salary: float, sales_amount: float):
        super().__init__(emp_id, name, base_salary)
        self.sales_amount = sales_amount


    def calculate_bonus(self) -> float:
        return self.sales_amount * 0.05

# Manager（经理）：奖金固定为 3000
class Manager(Employee):

    def calculate_bonus(self) -> float:
        return 3000

# Programmer（程序员）：奖金 = 完成项目数 × 500  -----> 扩充属性: 完成项目数 projects_completed
class Programmer(Employee):
    projects_completed: int
    """完成项目数 """
    
    def __init__(self, /, emp_id:str, name: str, base_salary: float, projects_completed: int):
        super().__init__(emp_id, name, base_salary)
        self.projects_completed = projects_completed

    def calculate_bonus(self) -> float:
        return self.projects_completed * 500.0


if __name__ == "__main__":
    employees = [
        Salesman(emp_id ="S001", name= "张三", base_salary= 5000, sales_amount= 5000),
        Manager(emp_id ="M001", name= "李四", base_salary= 5000),
        Programmer(emp_id ="P001", name= "王五", base_salary= 5000, projects_completed = 3)
    ]

    print("=" * 70)
    print("员工工资表")
    print("=" * 70)
    for e in employees:
        e.show_info()
    print("=" * 70)
