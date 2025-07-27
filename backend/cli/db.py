import typer

cli_app = typer.Typer(help="Database migrations and tools.")


@cli_app.command(help="Update database to latest schema.")
def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


# TODO: Remove this workaround once Typer merges this PR: https://github.com/fastapi/typer/pull/1240
@cli_app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()
