# This is just an example/test for providing a CLI
# With some work it could be used as the entrypoint for the container...
import typer
import uvicorn

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def initdb() -> None:
    print("Hello World")


@cli.command()
def serve() -> None:
    from app.main import app

    uvicorn.run(app, host="0.0.0.0", port=8000)


def run() -> None:
    cli()
