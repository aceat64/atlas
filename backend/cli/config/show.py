import typer
from rich import print
from rich.syntax import Syntax

from .toml import dict_to_toml
from .utils import load_config

cli_app = typer.Typer()


@cli_app.command(help="View the current config.")
def show() -> None:
    settings = load_config().model_dump()
    print(Syntax(code=dict_to_toml(settings), lexer="toml", theme="ansi_dark", background_color="default"))
