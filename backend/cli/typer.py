import os
from importlib.metadata import metadata
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from pydantic import ValidationError
from rich import print_json

from app.core.config import Settings
from app.core.logging import setup_logging

project_metadata = metadata("atlas")
default_config_files = [
    "/config/settings.toml",
    f"{Path(__file__).parent.parent.resolve()}/settings.toml",
]

app = typer.Typer(no_args_is_help=True, help=project_metadata["Summary"])


def version_callback(value: bool) -> None:
    if value:
        print(f"ATLAS {project_metadata['Version']}")
        raise typer.Exit()


@app.command(help="Run the ATLAS backend.")
def serve(reload: Annotated[bool, typer.Option()] = False) -> None:
    settings = Settings()
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        uds=settings.server.uds,
        forwarded_allow_ips=settings.server.forwarded_allow_ips,
        reload=reload,
        log_config=None,
    )


@app.command(help="Update database to latest schema.")
def migrate_db() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@app.command(help="View the current config.")
def config() -> None:
    print_json(Settings().model_dump_json())


@app.command(help="View the configuration schema.")
def config_schema() -> None:
    print_json(data=Settings().model_json_schema())


@app.command(help="Generate an example TOML config file.")
def config_example() -> None:
    from cli.toml import json_schema_to_toml

    schema = Settings().model_json_schema()
    print(json_schema_to_toml(schema))


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the version and exit.", callback=version_callback),
    ] = False,
    config_file: Annotated[
        Path | None,
        typer.Option(
            show_default=", ".join([file for file in default_config_files]),
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

    try:
        settings = Settings()
    except ValidationError as e:
        print(f"Invalid configuration: {e.error_count()} validation errors")
        for error in e.errors():
            print()
            print(".".join([str(value) for value in error["loc"]]))
            print(f"\tInput: {error['input']}")
            print(f"\t{error['msg']}")
        raise typer.Exit(1) from None
    setup_logging(settings)
