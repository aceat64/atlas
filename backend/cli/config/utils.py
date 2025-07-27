import typer
from pydantic import ValidationError
from rich.console import Console

from app.core.config import Settings

err_console = Console(stderr=True)


def load_config() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        err_console.print(f"Invalid configuration: {e.error_count()} validation errors")
        for error in e.errors():
            err_console.print()
            err_console.print(".".join([str(value) for value in error["loc"]]))
            err_console.print(f"\tInput: {error['input']}")
            err_console.print(f"\t{error['msg']}")
        raise typer.Exit(1) from None
