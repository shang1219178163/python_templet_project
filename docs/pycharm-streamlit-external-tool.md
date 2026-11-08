# PyCharm 右键启动 Streamlit（External Tools）

适用环境：macOS + PyCharm 2026.2 + 本项目（`uv` + `streamlit`）。

## 一、配置步骤

1. 打开 **PyCharm → Settings（⌘,）→ Tools → External Tools**。
2. 点击左上角 `+`，按下表填写：

| 配置项 | 值 |
| --- | --- |
| Name | `Run Streamlit` |
| Description | `用当前文件启动 Streamlit` |
| Program | `/usr/local/bin/uv` |
| Arguments | `run streamlit run "$FilePath$"` |
| Working directory | `$ProjectFileDir$` |
| Environment variables | `PYTHONPATH=$ProjectFileDir$` |

3. 在 **Show in** 区域勾选：
   - `Main menu`（可选）
   - `Project views`（项目树右键）
   - `Editor popup menu`（编辑器右键）
   - `Search popup`（可选）
4. 在 **Advanced Options** 区域勾选：
   - `Open console`：运行日志显示在 Run 控制台。
   - `Synchronize files after run`：运行结束后自动同步文件。
5. 点击 **OK / Apply** 保存，无需重启 IDE。

> 关键点：工作目录必须是**项目根目录**，并通过 `PYTHONPATH` 把根目录加入模块搜索路径。因为 `page/streamlit_demo.py` 会导入根目录下的 `base_widget` 包，Streamlit 默认只把脚本所在目录（`page/`）加入 `sys.path`，找不到根目录的模块。

## 二、使用方式

在项目树或编辑器中右键任意文件 → **External Tools → Run Streamlit**，等价于执行：

```bash
cd "$ProjectFileDir$"
PYTHONPATH="$ProjectFileDir$" /usr/local/bin/uv run streamlit run "$FilePath$"
```

Streamlit 启动后会默认打开浏览器，地址为 `http://localhost:8501`。

## 三、常用可选参数

需要时把参数追加到 Arguments 末尾，例如：

```text
run streamlit run "$FilePath$" --server.port 8502
```

| 参数 | 用途 |
| --- | --- |
| `--server.port 8502` | 8501 端口被占用时换端口 |
| `--server.headless true` | 不自动打开浏览器 |
| `--server.address 0.0.0.0` | 允许局域网访问 |

## 四、常见问题

- **报错 `ModuleNotFoundError: No module named 'base_widget'`**：`Working directory` 仍是文件所在目录，或缺少 `PYTHONPATH`。按上表改为项目根目录并添加 `PYTHONPATH=$ProjectFileDir$`。
- **报错“工作目录 `.../page ` 不存在”**：`Working directory` 末尾多了空格。删掉空格，确保严格为 `$ProjectFileDir$`；`Program`、`Arguments` 末尾也不要有无意义的空格。
- **提示找不到 `uv`**：确认 Program 使用绝对路径（`which uv` 可查，本机为 `/usr/local/bin/uv`）。从 Dock 启动 PyCharm 时 PATH 可能不完整，因此不要只写 `uv`。
- **`PYTHONPATH` 宏没有展开**：可先尝试重启 IDE；仍无效时直接把该栏写成项目根目录的绝对路径，例如 `/Users/shang/GitHub/python_templet_project`。
- **端口被占用**：使用 `lsof -i :8501` 查看占用进程，或追加 `--server.port` 换端口。
- **非 `.py` 文件也显示该菜单**：这是 External Tools 的固有限制，无法按扩展名过滤；只有开发 PyCharm 插件才能做到“仅 `.py` 显示”的一级右键菜单。
- **首次运行较慢**：`uv run` 会先校验/同步依赖，属正常现象。
- **控制台出现 `VIRTUAL_ENV ... does not match` 警告**：无害，`uv` 会忽略外部 `VIRTUAL_ENV` 并改用项目 `.venv`。若想彻底避免，可把 Program 改为 `<项目根>/.venv/bin/python`，Arguments 改为 `-m streamlit run "$FilePath$"`。

## 五、为什么不能把工作目录设成 `$FileDir$`

本项目的页面位于 `page/`，但公共组件包 `base_widget` 位于项目根目录。`streamlit run page/streamlit_demo.py` 只会把 `page/` 加入 `sys.path`，不会加入项目根目录，因此会报 `ModuleNotFoundError`。README 中的启动命令同样是：

```bash
PYTHONPATH=. .venv/bin/streamlit run page/streamlit_demo.py
```

即：**从项目根目录启动，并把根目录加入 `PYTHONPATH`**。外部工具按同样方式配置即可。同时，工作目录固定在项目根目录，也能让 `assets/`、`data/` 等相对路径按项目约定解析。
