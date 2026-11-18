# Pydantic 脚本启动慢几百毫秒：logfire 插件被自动加载

## 现象

运行 `app/page/codable.py` 这种「定义一两个 `BaseModel`」的小脚本，也要等一会儿才出结果；
代码本身只有几十行，没有网络请求、没有大文件读写。

## 实测数据

用 `-X importtime` 拆解启动过程（本机）：

| 项目 | 耗时 |
| --- | --- |
| 脚本总耗时 | 0.67s |
| 其中 `app.model.book`（定义 `Book` 类） | **446ms** |
| 其中 `pydantic` 本身 | 51ms |
| 其中 `logfire` + `opentelemetry` + `requests` | ≈ 350ms |

一条命令即可复现：

```bash
time .venv/bin/python -c "from pydantic import BaseModel; class X(BaseModel): a: int"
# 0.59s

time PYDANTIC_DISABLE_PLUGINS=__all__ .venv/bin/python -c "from pydantic import BaseModel; class X(BaseModel): a: int"
# 0.19s
```

## 原因

Pydantic V2 在**第一次定义模型类**时，会扫描所有已安装包注册的 `pydantic` 插件入口
（见 `.venv/lib/python3.13/site-packages/pydantic/plugin/_loader.py`）：

```python
PYDANTIC_ENTRY_POINT_GROUP = 'pydantic'

def get_plugins() -> Iterable[PydanticPluginProtocol]:
    disabled_plugins = os.getenv('PYDANTIC_DISABLE_PLUGINS')
    ...
    for dist in importlib_metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group != PYDANTIC_ENTRY_POINT_GROUP:
                continue
            _plugins[entry_point.value] = entry_point.load()
```

本项目的 `pydantic-ai` 带进来了 `logfire-sdk`，它注册了一个插件：

```text
logfire-sdk -> logfire-plugin = logfire.integrations.pydantic:plugin
```

于是**每个**定义 `BaseModel` 子类的脚本都会连带导入 `logfire`、`opentelemetry`、`requests`，
几百毫秒就这么没了。注意这不是某个脚本的问题，所有用 Pydantic 的脚本都有这份成本。

## 解决方案

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| **A. PyCharm 模板加环境变量** | Run/Debug Configurations → **Edit configuration templates** → Python → Environment variables 填 `PYDANTIC_DISABLE_PLUGINS=__all__` | 只影响 PyCharm 里的运行 |
| **B. 写进 `sitecustomize.py`**（本项目采用） | `os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")`，从项目根启动的进程自动生效 | 全局静默生效，需要在文件头注释说明 |
| **C. 去掉 `pydantic-ai`** | 从依赖中移除，`logfire` 就不会进环境 | 改动最大，且会失去该库 |

本项目没有用 logfire 做可观测性，禁用它的 Pydantic 插件不损失任何功能 —— 它只是 `pydantic-ai` 的附带依赖。

## 自己排查类似问题的方法

```bash
PYTHONPATH=. .venv/bin/python -X importtime app/page/codable.py 2> importtime.log >/dev/null
```

`importtime.log` 每行形如 `import time: self | cumulative | 模块名`（单位是微秒，缩进表示嵌套层级）。
按 cumulative 排序，最前面的几行就是启动开销的来源；再用缩进逐级往上找，就能定位到「是谁把谁带进来的」。
