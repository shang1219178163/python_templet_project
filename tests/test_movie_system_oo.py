"""电影信息管理系统（ConsoleCrud 版）需求验收测试。

运行方式（项目根目录）：
    python -m unittest tests.test_movie_system_oo -v
    python -m unittest discover -s tests -v
    python -m tests.test_movie_system_oo
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from app.page.curd.movie_system_oo import Movie, MovieSystem


def run_with_inputs(system: MovieSystem, inputs: list[str]) -> str:
    """按顺序喂入输入，运行菜单并返回打印内容。"""
    buffer = io.StringIO()
    with patch("builtins.input", side_effect=inputs), redirect_stdout(buffer):
        system.run()
    return buffer.getvalue()


def seed(system: MovieSystem, name: str, *, price: float = 30.0, score: float = 8.0) -> None:
    """直接写入一行数据，用于不关心录入流程的用例。"""
    system.crud.data[name] = {"director": "导演", "actor": "演员", "price": price, "score": score}


class MovieTest(unittest.TestCase):
    """Movie：初始化、字符串格式与信息更新。"""

    def test_str_format(self) -> None:
        movie = Movie("流浪地球", "郭帆", "吴京", 45.0, 8.6)
        self.assertEqual(
            str(movie),
            "电影名: 流浪地球 | 导演: 郭帆 | 主演: 吴京 | 票价: 45.0 | 评分: 8.6",
        )

    def test_update_info(self) -> None:
        movie = Movie("流浪地球", "郭帆", "吴京", 45.0, 8.6)
        movie.update_info("郭帆", "屈楚萧", 50.0, 8.8)
        self.assertEqual((movie.director, movie.actor, movie.price, movie.score), ("郭帆", "屈楚萧", 50.0, 8.8))
        self.assertEqual(movie.name, "流浪地球")  # 电影名不可修改


class MovieSystemBase(unittest.TestCase):
    """MovieSystem 测试公共夹具。"""

    def setUp(self) -> None:
        self.system = MovieSystem()


class MovieSystemInitTest(MovieSystemBase):
    """初始化与类属性。"""

    def test_class_attributes(self) -> None:
        self.assertEqual(MovieSystem.system_name, "电影信息管理系统")
        self.assertEqual(MovieSystem.system_version, "1.0")

    def test_starts_empty(self) -> None:
        self.assertEqual(self.system.crud.data, {})
        self.assertEqual(self.system.movie_list, [])


class MovieSystemAddTest(MovieSystemBase):
    """3.1 添加电影。"""

    def test_add_success(self) -> None:
        output = run_with_inputs(self.system, ["1", "流浪地球", "郭帆", "吴京", "45", "8.6", "7"])
        self.assertIn("添加成功：流浪地球", output)
        self.assertEqual(
            self.system.crud.data["流浪地球"],
            {"director": "郭帆", "actor": "吴京", "price": 45.0, "score": 8.6},
        )
        movie = self.system.movie_list[0]
        self.assertEqual((movie.name, movie.actor, movie.price, movie.score), ("流浪地球", "吴京", 45.0, 8.6))

    def test_add_duplicate_rejected(self) -> None:
        inputs = [
            "1", "流浪地球", "郭帆", "吴京", "45", "8.6",
            "1", "流浪地球",
            "7",
        ]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("电影已存在，请执行修改操作", output)
        self.assertEqual(len(self.system.crud.data), 1)

    def test_add_price_must_be_positive(self) -> None:
        # 0 不合法，ConsoleCrud 会提示后重新录入
        inputs = ["1", "某电影", "导演", "演员", "0", "45", "8", "7"]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("票价必须大于 0", output)
        self.assertEqual(self.system.crud.data["某电影"]["price"], 45.0)

    def test_add_score_must_be_in_range(self) -> None:
        inputs = ["1", "某电影", "导演", "演员", "30", "11", "8", "7"]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("评分必须在 0-10 之间", output)
        self.assertEqual(self.system.crud.data["某电影"]["score"], 8.0)

    def test_add_score_boundaries_accepted(self) -> None:
        run_with_inputs(self.system, ["1", "零分片", "导演", "演员", "1", "0", "7"])
        run_with_inputs(self.system, ["1", "满分片", "导演", "演员", "1", "10", "7"])
        self.assertEqual(self.system.crud.data["零分片"]["score"], 0.0)
        self.assertEqual(self.system.crud.data["满分片"]["score"], 10.0)

    def test_add_non_numeric_price_reprompts(self) -> None:
        inputs = ["1", "某电影", "导演", "演员", "abc", "45", "8", "7"]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("请输入数字", output)
        self.assertEqual(self.system.crud.data["某电影"]["price"], 45.0)

    def test_add_empty_director_reprompts(self) -> None:
        inputs = ["1", "某电影", "", "导演", "演员", "30", "8", "7"]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("导演不能为空", output)
        self.assertEqual(self.system.crud.data["某电影"]["director"], "导演")


class MovieSystemUpdateTest(MovieSystemBase):
    """3.2 修改电影。"""

    def test_update_success(self) -> None:
        run_with_inputs(self.system, ["1", "流浪地球", "郭帆", "吴京", "45", "8.6", "7"])
        inputs = ["2", "流浪地球", "郭帆", "屈楚萧", "50", "8.8", "7"]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("修改成功：流浪地球", output)
        self.assertEqual(
            self.system.crud.data["流浪地球"],
            {"director": "郭帆", "actor": "屈楚萧", "price": 50.0, "score": 8.8},
        )

    def test_update_missing_movie(self) -> None:
        output = run_with_inputs(self.system, ["2", "不存在", "7"])
        self.assertIn("电影不存在", output)
        self.assertEqual(self.system.crud.data, {})


class MovieSystemDeleteTest(MovieSystemBase):
    """3.3 删除电影。"""

    def test_delete_success(self) -> None:
        run_with_inputs(self.system, ["1", "流浪地球", "郭帆", "吴京", "45", "8.6", "7"])
        output = run_with_inputs(self.system, ["3", "流浪地球", "7"])
        self.assertIn("删除成功：流浪地球", output)
        self.assertEqual(self.system.crud.data, {})

    def test_delete_missing_movie(self) -> None:
        output = run_with_inputs(self.system, ["3", "不存在", "7"])
        self.assertIn("电影不存在", output)


class MovieSystemQueryTest(MovieSystemBase):
    """3.4 精确查询与查询所有。"""

    def test_query_found(self) -> None:
        run_with_inputs(self.system, ["1", "流浪地球", "郭帆", "吴京", "45", "8.6", "7"])
        output = run_with_inputs(self.system, ["4", "流浪地球", "7"])
        self.assertIn("电影名: 流浪地球 | 导演: 郭帆 | 主演: 吴京 | 票价: 45.0 | 评分: 8.6", output)

    def test_query_missing(self) -> None:
        seed(self.system, "流浪地球")
        output = run_with_inputs(self.system, ["4", "流浪", "7"])
        self.assertIn("电影不存在", output)

    def test_list_movies_empty(self) -> None:
        output = run_with_inputs(self.system, ["5", "7"])
        self.assertIn("暂无电影", output)

    def test_list_movies_all(self) -> None:
        seed(self.system, "流浪地球", price=45.0)
        seed(self.system, "三体", price=30.0)
        output = run_with_inputs(self.system, ["5", "7"])
        self.assertIn("流浪地球", output)
        self.assertIn("三体", output)
        self.assertIn("共 2 部电影", output)


class MovieSystemTopRatedTest(MovieSystemBase):
    """3.5 查询评分最高电影。"""

    def test_top_rated_empty(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            movies = self.system.top_rated_movie()
        self.assertEqual(movies, [])
        self.assertIn("暂无电影", buffer.getvalue())

    def test_top_rated_single(self) -> None:
        seed(self.system, "流浪地球", score=8.6)
        seed(self.system, "三体", score=7.5)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            movies = self.system.top_rated_movie()
        self.assertEqual([movie.name for movie in movies], ["流浪地球"])

    def test_top_rated_tie_returns_all(self) -> None:
        seed(self.system, "流浪地球", score=8.6)
        seed(self.system, "星际穿越", score=8.6)
        seed(self.system, "三体", score=7.5)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            movies = self.system.top_rated_movie()
        output = buffer.getvalue()
        self.assertEqual([movie.name for movie in movies], ["流浪地球", "星际穿越"])
        self.assertIn("流浪地球", output)
        self.assertIn("星际穿越", output)


class MovieSystemRunTest(MovieSystemBase):
    """菜单流程集成。"""

    def test_run_add_query_top_and_exit(self) -> None:
        inputs = [
            "1", "流浪地球", "郭帆", "吴京", "45", "8.6",
            "4", "流浪地球",
            "6",
            "7",
        ]
        output = run_with_inputs(self.system, inputs)
        self.assertIn("添加成功：流浪地球", output)
        self.assertIn("电影名: 流浪地球", output)
        self.assertIn("退出成功", output)
        self.assertEqual(len(self.system.crud.data), 1)

    def test_run_invalid_option(self) -> None:
        output = run_with_inputs(self.system, ["9", "7"])
        self.assertIn("不支持该操作！", output)


if __name__ == "__main__":
    unittest.main()
