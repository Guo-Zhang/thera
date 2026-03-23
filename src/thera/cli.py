"""
Thera CLI - 使用 Typer 重写
"""

import typer
from pathlib import Path
from typing import Optional

from thera.refresh import refresh as do_refresh

app = typer.Typer(no_args_is_help=True)


@app.command()
def refresh(
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式，不执行实际变更"),
    submodule: Optional[str] = typer.Argument(
        None, help="子模块名（如 journal, archive）"
    ),
):
    """
    同步子模块并提交推送主仓库。

    用法:
        thera refresh              # 同步所有子模块
        thera refresh journal     # 只同步 docs/journal
        thera refresh --dry-run   # 预览所有
    """
    result = do_refresh(Path("."), dry_run=dry_run, submodule=submodule)

    if result.updated_submodules:
        for sm in result.updated_submodules:
            typer.echo(f"✓ {sm}: 已更新")

    if result.success:
        if result.commit_sha:
            typer.echo(f"✓ 已提交并推送 ({result.commit_sha})")
        else:
            typer.echo(f"✓ {result.message}")
        raise typer.Exit(0)
    else:
        typer.echo(f"[FAIL] {result.message}")
        if result.error:
            typer.echo(f"  Error: {result.error}")
        raise typer.Exit(1)


def main():
    app()
