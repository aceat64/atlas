from pathlib import Path
from typing import Annotated

import typer

from app.core.logging import setup_logging
from cli.config.utils import load_config

cli_app = typer.Typer(help="Database migrations and tools.")


@cli_app.command(help="Update database to latest schema.")
def migrate(ctx: typer.Context, revision: Annotated[str, typer.Argument()] = "head") -> None:
    from alembic import command
    from alembic.config import Config

    load_config(ctx.obj["config_file"])
    setup_logging()
    alembic_cfg = Config(f"{Path(__file__).parent.parent.resolve()}/alembic.ini")
    command.upgrade(alembic_cfg, revision)


# TODO: Remove this workaround once Typer merges this PR: https://github.com/fastapi/typer/pull/1240
@cli_app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()
