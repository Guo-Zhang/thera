# submodule-sync

检测并同步子模块的远程更新。

## 使用方法

```bash
# 进入 thera 目录
cd src/thera

# 激活虚拟环境
source .venv/bin/activate

# 检测远程更新
python src/thera/cli.py submodule-sync --check

# 同步指定子模块
python src/thera/cli.py submodule-sync --sync "docs/tutorial,src/thera"

# 同步所有子模块
python src/thera/cli.py submodule-sync --sync-all
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
$ python src/thera/cli.py submodule-sync --check
子模块数: 2
  docs/tutorial: 5e622bf (已是最新)
  src/thera: c38fd399 (已是最新)

# 检测到更新
$ python src/thera/cli.py submodule-sync --check
子模块数: 2
  docs/tutorial: abc1234 (有更新)
  src/thera: def5678 (有更新)

# 同步全部
$ python src/thera/cli.py submodule-sync --sync-all
[OK] 同步完成
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 无更新或全部同步成功 |
| 1 | 检测到更新（--check 模式）或同步失败 |

## 状态机集成

submodule-sync 与状态机集成：

- 同步成功 → 状态转移至 SYNCED
- 仅在 CLEAN_AND_CONSISTENT 状态下允许同步
