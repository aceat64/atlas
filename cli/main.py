from importlib.metadata import metadata
from pathlib import Path
from typing import Annotated

import typer

from app.core.config import settings

from .config import cli_app as config_app
from .db import cli_app as db_app
from .serve import cli_app as serve_app

project_metadata = metadata("atlas")
cli_app = typer.Typer(help=project_metadata["Summary"])


def version_callback(value: bool) -> None:
    if value:
        print(f"ATLAS {project_metadata['Version']}")
        raise typer.Exit()


@cli_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show the version and exit.", callback=version_callback, is_eager=True),
    ] = False,
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config-file",
            "-c",
            help="Path to a TOML configuration file.",
            show_default=", ".join(settings.model_config["toml_file"]),
            envvar="ATLAS_CONFIG_FILE",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    ctx.obj = {"config_file": str(config_file) if config_file else None}
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()


cli_app.add_typer(config_app, name="config")
cli_app.add_typer(db_app, name="db")
cli_app.add_typer(serve_app)
