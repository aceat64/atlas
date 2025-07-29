import typer
from rich import print
from rich.syntax import Syntax
from tomlkit import document

from app.core.config import AppSettings

from .utils import process_model

cli_app = typer.Typer()


@cli_app.command(help="Generate an example TOML config file.")
def example() -> None:
    example_settings = AppSettings.model_construct()
    example_settings.model_config["toml_file"] = None
    example_settings.model_config["env_prefix"] = "ATLAS_EXAMPLE_"
    example_settings.__init__()  # type: ignore

    print(
        Syntax(
            code=process_model(example_settings, document(), comments=True).as_string(),
            lexer="toml",
            theme="ansi_dark",
            background_color="default",
        )
    )
