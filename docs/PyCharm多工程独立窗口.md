# PyCharm 能否每个工程都是单独的窗口？

可以。PyCharm 原生支持「一个工程一个窗口」，改一个设置就行。

## 设置路径

**Settings → Appearance & Behavior → System Settings → Project**

找到 **Open project in**，把默认行为改成：

| 选项 | 效果 |
| --- | --- |
| `Ask` | 每次打开项目时弹窗问你 |
| `New window` | 每个工程独立窗口（推荐） |
| `Current window` | 新项目挤掉当前窗口 |

> 旧版 UI 里这个选项叫「Confirm opening of projects in new window」，位于 **Settings → Appearance & Behavior → System Settings**。

## 临时指定（不改全局）

`File → Open…` 选中工程目录后，对话框底部有 **Open in new window** 复选框，勾上就这一次开新窗口。从欢迎屏（Welcome to PyCharm）打开项目时同理。

## macOS 上的使用细节

- 每个工程窗口共享**同一个 PyCharm 进程**（索引、内存池是共用的），所以一个工程建索引时其他窗口也可能变慢；但窗口之间互不影响，关一个不会影响另一个。
- 用 `⌘ + \`` 在多个工程窗口之间轮换，或从 **Window** 菜单直接点项目名。
- Dock 图标底下只有一个 PyCharm —— macOS 不提供「每个窗口一个 Dock 图标」。

## 如果想让每个工程是**完全独立的进程**

比如想单独重启某个工程、给不同工程配不同 JVM 参数，光开窗口不够，需要多实例：

```bash
open -n -a "PyCharm.app"                              # 再拉起一个独立 PyCharm 进程
open -n -a "PyCharm.app" --args /path/to/project      # 指定要打开的工程目录
```

多实例的代价是每个进程都要重新建索引、内存翻倍，一般**不建议**日常这么用，开多个窗口已经足够。

## 一点提醒

这个设置只影响**之后新打开**的工程。当前已经打开的工程窗口不会变化；下次从「最近项目」里打开别的工程时，就会自动开新窗口了。

---

> 记录日期：2026-11-18 18:45
