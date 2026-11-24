"""空 sitecustomize：覆盖 PyCharm 注入的绘图后端 sitecustomize。

PyCharm 每次运行会把 helpers/pycharm_plotly_backend 等目录前置到 PYTHONPATH，
其中 sitecustomize.py 会 import datalore.display，连带导入 pandas/altair，
使解释器启动多花 2~5 秒。项目根目录在 PYTHONPATH 最前，本文件会优先被导入，
从而让 PyCharm 那个 sitecustomize 不再执行。

副作用：PyCharm Plots 工具窗口不再接管 plotly/matplotlib 渲染。
需要看图时删除本文件即可恢复。

另外这里顺手关掉了 Pydantic 的插件加载：Pydantic V2 在第一次定义模型类时会扫描所有
已安装包的 pydantic 插件入口，本项目经 pydantic-ai 装进来的 logfire-sdk 注册了一个插件，
导致每次启动多导入 logfire/opentelemetry/requests（约 0.3~0.5 秒）。本项目不用 logfire，
设为 __all__ 后跳过多余导入；若以后确实要用 logfire 的 Pydantic 埋点，删掉下面这行即可。
详见 docs/Pydantic启动变慢.md。
"""

import os

os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")
