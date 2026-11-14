"""空 sitecustomize：覆盖 PyCharm 注入的绘图后端 sitecustomize。

PyCharm 每次运行会把 helpers/pycharm_plotly_backend 等目录前置到 PYTHONPATH，
其中 sitecustomize.py 会 import datalore.display，连带导入 pandas/altair，
使解释器启动多花 2~5 秒。项目根目录在 PYTHONPATH 最前，本文件会优先被导入，
从而让 PyCharm 那个 sitecustomize 不再执行。

副作用：PyCharm Plots 工具窗口不再接管 plotly/matplotlib 渲染。
需要看图时删除本文件即可恢复。
"""
