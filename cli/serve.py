from typing import Annotated

import structlog
import typer
import uvicorn

from app.core.config import settings
from cli.config.utils import load_config

log = structlog.stdlib.get_logger("cli")

cli_app = typer.Typer()


@cli_app.command(help="Run the ATLAS server.")
def serve(ctx: typer.Context, reload: Annotated[bool, typer.Option()] = False) -> None:
    load_config(ctx.obj["config_file"])
    if reload:
        log.info("Reload enabled")
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        uds=settings.server.uds,
        forwarded_allow_ips=settings.server.forwarded_allow_ips,
        reload=reload,
        reload_excludes=["cli/*"],
        log_config=None,  # We setup logging ourselves and don't want uvicorn to mess it up
    )
