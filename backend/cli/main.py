# This is just an example/test for providing a CLI
# With some work it could be used as the entrypoint for the container...
from enum import Enum
from importlib.metadata import metadata
from typing import Annotated

import typer
import uvicorn
from rich import print, print_json

project_metadata = metadata("atlas")

app = typer.Typer(no_args_is_help=True, help=project_metadata["Summary"])


class LogLevel(str, Enum):
    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"
    trace = "trace"


def version_callback(value: bool) -> None:
    if value:
        print(f"ATLAS {project_metadata['Version']}")
        raise typer.Exit()


@app.command(help="Run the ATLAS backend.")
def serve(
    host: Annotated[str, typer.Option(help="Bind socket to this host.")] = "0.0.0.0",
    port: Annotated[
        int, typer.Option(help="Bind socket to this port. If 0, an available port will be picked.")
    ] = 8000,
    log_level: Annotated[LogLevel, typer.Option()] = LogLevel.info,
) -> None:
    from app.main import app

    uvicorn.run(app, host=host, port=port, log_level=log_level)


@app.command(help="Update database to latest schema.")
def migrate_db() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@app.command(help="View the current config.")
def config() -> None:
    from pydantic import ValidationError

    try:
        from app.core.config import settings
    except ValidationError as e:
        print(e)
        raise typer.Exit(1) from None

    print_json(settings.model_dump_json())


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", callback=version_callback)] = False,
) -> None:
    pass


app()
