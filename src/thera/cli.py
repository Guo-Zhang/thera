"""
Thera CLI - 使用 Typer 重写
"""

import typer
from pathlib import Path
from typing import Optional

from thera.refresh import refresh

app = typer.Typer(no_args_is_help=True)


@app.command()
def refresh(
    repo: Path = typer.Argument(".", help="仓库根目录"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式，不执行实际变更"),
):
    """
    同步子模块并提交推送主仓库。
    """
    result = refresh(repo, dry_run=dry_run)

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
