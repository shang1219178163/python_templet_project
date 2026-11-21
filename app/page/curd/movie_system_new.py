"""电影信息管理系统（面向对象版，基于 ConsoleCrud）。

对应作业题 2 需求：Movie + MovieSystem，支持添加、修改、删除、精确查询、
查询所有、查询评分最高（并列一并输出）。
"""

from collections.abc import Mapping

from app.util.console_crud import ConsoleCrud, CrudField, CrudRow


class Movie:
    """一部电影的信息，以及展示、更新能力。"""

    def __init__(self, name: str, director: str, actor: str, price: float, score: float) -> None:
        self.name = name
        self.director = director
        self.actor = actor
        self.price = price
        self.score = score

    def __str__(self) -> str:
        return (
            f"电影名: {self.name} | 导演: {self.director} | 主演: {self.actor}"
            f" | 票价: {self.price} | 评分: {self.score}"
        )

    def update_info(self, director: str, actor: str, price: float, score: float) -> None:
        """更新除电影名以外的信息；电影名作为唯一标识不参与修改。"""
        self.director = director
        self.actor = actor
        self.price = price
        self.score = score


def format_movie(name: str, row: CrudRow) -> str:
    """把一行字典数据按 Movie.__str__ 的格式展示。"""
    return str(Movie(name, row["director"], row["actor"], row["price"], row["score"]))


def summarize_movies(data: Mapping[str, CrudRow]) -> str:
    """查询全部时的汇总行：数量 + 总票价。"""
    total_price = sum(row["price"] for row in data.values())
    return f"共 {len(data)} 部电影，总票价 {total_price:g}"


class MovieSystem:
    """电影信息管理系统：增删改查委托 ConsoleCrud，另行实现评分最高查询。"""

    system_name = "电影信息管理系统"
    system_version = "1.0"

    def __init__(self) -> None:
        self.crud = ConsoleCrud(
            title=self.system_name,
            entity="电影",
            key_prompt="电影名：",
            fields={
                "director": CrudField("导演：", ConsoleCrud.read_str, lambda v: bool(v), "导演不能为空"),
                "actor": CrudField("主演：", ConsoleCrud.read_str, lambda v: bool(v), "主演不能为空"),
                "price": CrudField("票价：", ConsoleCrud.read_float, lambda v: v > 0, "票价必须大于 0"),
                "score": CrudField("评分：", ConsoleCrud.read_float, lambda v: 0 <= v <= 10, "评分必须在 0-10 之间"),
            },
            format_row=format_movie,
            summarize=summarize_movies,
            empty_hint="暂无电影",
        )

    @property
    def movie_list(self) -> list[Movie]:
        """把 ConsoleCrud 的字典数据转换成 Movie 列表。"""
        return [
            Movie(name, row["director"], row["actor"], row["price"], row["score"])
            for name, row in self.crud.data.items()
        ]

    # ---------------- 业务方法 ----------------

    def top_rated_movie(self) -> list[Movie]:
        """查询评分最高的电影，并列最高分一并返回。"""
        movie_list = self.movie_list
        if not movie_list:
            print("暂无电影")
            return []
        top_score = max(movie.score for movie in movie_list)
        top_movies = [movie for movie in movie_list if movie.score == top_score]
        for movie in top_movies:
            print(movie)
        return top_movies

    # ---------------- 菜单 ----------------

    def run(self) -> None:
        """显示菜单并循环接收用户操作，选 7 退出。"""
        while True:
            print(
                "\n==================== 电影信息管理系统 ====================\n"
                "1. 添加电影   2. 修改电影   3. 删除电影\n"
                "4. 查询指定电影  5. 查询所有电影\n"
                "6. 查询评分最高电影  7. 退出系统\n"
                "========================================================="
            )
            oper = input("请输入对应操作编号（1-7）：").strip()
            match oper:
                case "1":
                    self.crud.add()
                case "2":
                    self.crud.update()
                case "3":
                    self.crud.delete()
                case "4":
                    self.crud.query()
                case "5":
                    self.crud.show()
                case "6":
                    self.top_rated_movie()
                case "7":
                    print("退出成功，欢迎下次使用！")
                    break
                case _:
                    print("不支持该操作！")


if __name__ == "__main__":
    MovieSystem().run()
