from typing import Annotated

import typer
import uvicorn

from app.core.logging import setup_logging

from .config.utils import load_config

cli_app = typer.Typer()


@cli_app.command(help="Run the ATLAS backend.")
def serve(reload: Annotated[bool, typer.Option()] = False) -> None:
    settings = load_config()
    setup_logging(settings)
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        uds=settings.server.uds,
        forwarded_allow_ips=settings.server.forwarded_allow_ips,
        reload=reload,
        log_config=None,  # We already setup logging and don't want uvicorn to mess it up
    )
