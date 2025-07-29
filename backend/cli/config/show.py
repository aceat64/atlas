from typing import Annotated

import typer
from rich import print
from rich.syntax import Syntax
from tomlkit import document

from app.core.config import settings

from .utils import load_config, process_model

cli_app = typer.Typer()


@cli_app.command(help="View the current config.")
def show(
    ctx: typer.Context,
    comments: Annotated[
        bool,
        typer.Option(help="Show comments in the generated toml file."),
    ] = True,
) -> None:
    load_config(ctx.obj["config_file"])

    print(
        Syntax(
            code=process_model(settings, document(), comments=comments).as_string(),
            lexer="toml",
            theme="ansi_dark",
            background_color="default",
        )
    )
