import os
from importlib.metadata import metadata
from pathlib import Path
from typing import Annotated

import typer

from app.core.config import default_config_files

from .config import cli_app as config_app
from .db import cli_app as db_app
from .serve import cli_app as serve_app

project_metadata = metadata("atlas")


def version_callback(value: bool) -> None:
    if value:
        print(f"ATLAS {project_metadata['Version']}")
        raise typer.Exit()


cli_app = typer.Typer(help=project_metadata["Summary"])


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
            show_default=", ".join(default_config_files),
            envvar="ATLAS_CONFIG_FILE",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    if config_file:
        # This is an ugly hack, but it works 🙈
        os.environ["ATLAS_CONFIG_FILE"] = str(config_file)
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()


cli_app.add_typer(config_app, name="config")
cli_app.add_typer(db_app, name="db")
cli_app.add_typer(serve_app)
