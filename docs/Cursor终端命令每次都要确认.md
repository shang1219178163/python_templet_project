# Cursor 终端命令每次都要确认

## 现象

Agent 执行终端命令时，几乎每次都会弹出确认，无法直接跑完。

## 原因

CLI 配置 `~/.cursor/cli-config.json` 里的 `approvalMode` 为 `allowlist`。

白名单模式下，只有 `permissions.allow` 里登记过的命令会直接执行。当前放行的是一组具体命令，例如 `git status`、`git diff`、`python3`、`.venv/bin/python`，不是全部 Shell。新命令，或以未登记程序开头的管道，都会再问一次。

`deny` 里的命令始终不会自动执行。当前 `deny` 为空。

## 处理

把审批模式改成全部自动执行。CLI 接受的取值只有两个：

| 值 | 行为 |
| --- | --- |
| `allowlist` | 只自动执行白名单内的命令 |
| `unrestricted` | 未写入 `deny` 的命令直接执行，等同 `--force` / `--yolo` |

已将配置改为：

```json
"approvalMode": "unrestricted"
```

改完后需要重新打开 CLI 会话，当前对话仍可能沿用旧配置。

若只想放行部分命令，保持 `allowlist`，把常用命令补进 `permissions.allow`，或写成 `Shell(**)`。
