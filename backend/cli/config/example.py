import typer
from rich import print
from rich.syntax import Syntax

from app.core.config import Settings

from .toml import json_schema_to_toml

cli_app = typer.Typer()


@cli_app.command(help="Generate an example TOML config file.")
def example() -> None:
    schema = Settings.model_json_schema()
    print(Syntax(code=json_schema_to_toml(schema), lexer="toml", theme="ansi_dark", background_color="default"))
