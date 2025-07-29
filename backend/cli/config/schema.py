import typer
from rich import print_json

from app.core.config import settings

cli_app = typer.Typer()


@cli_app.command(help="View the configuration schema.")
def schema() -> None:
    print_json(data=settings.model_json_schema())
