import typer

from .example import cli_app as example_app
from .schema import cli_app as schema_app
from .show import cli_app as show_app

cli_app = typer.Typer(help="Tools for working with ATLAS configuration.")
cli_app.add_typer(show_app)
cli_app.add_typer(example_app)
cli_app.add_typer(schema_app)


# TODO: Remove this workaround once Typer merges this PR: https://github.com/fastapi/typer/pull/1240
@cli_app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()
