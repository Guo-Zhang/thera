# submodule-sync

检测并同步子模块的远程更新。

## 使用方法

```bash
# 设置 PYTHONPATH
export PYTHONPATH=src/thera/src

# 检测远程更新
python3 src/thera/src/thera/cli.py submodule-sync --check

# 同步指定子模块
python3 src/thera/src/thera/cli.py submodule-sync --sync "docs/tutorial,src/thera"

# 同步所有子模块
python3 src/thera/src/thera/cli.py submodule-sync --sync-all
```

## 命令选项

| 选项 | 说明 |
|------|------|
| `--check` | 检测远程更新，显示有更新的子模块 |
| `--sync PATHS` | 同步指定子模块（逗号分隔） |
| `--sync-all` | 同步所有子模块 |
| `--repo PATH` | 指定仓库根目录（默认当前目录） |

## 示例

```bash
# 检测更新
$ python3 src/thera/src/thera/cli.py submodule-sync --check
检测子模块更新...
[OK] 所有子模块已是最新

# 检测到更新
$ python3 src/thera/src/thera/cli.py submodule-sync --check
检测子模块更新...

检测到以下子模块有更新：
  [UP] docs/tutorial (5e622bf)
  [UP] src/thera (c38fd399)

# 同步单个
$ python3 src/thera/src/thera/cli.py submodule-sync --sync docs/tutorial
同步 docs/tutorial...
[OK] docs/tutorial 同步成功

# 同步全部
$ python3 src/thera/src/thera/cli.py submodule-sync --sync-all
同步所有子模块...
[OK] 所有子模块同步完成
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无更新或全部同步成功 |
| 1 | 检测到更新（--check 模式）或同步失败 |
