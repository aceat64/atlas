from typing import Any

import typer
from pydantic import BaseModel, ValidationError
from rich.console import Console
from tomlkit import TOMLDocument, comment, item, nl, table
from tomlkit.items import Table

from app.core.config import settings

err_console = Console(stderr=True)


def load_config(filename: str | list[str] | None = None) -> None:
    if filename is not None:
        settings.model_config["toml_file"] = filename
    try:
        settings.__init__()  # type: ignore
    except ValidationError as e:
        err_console.print(f"[red underline]Invalid configuration:[/red underline] {e.error_count()} validation errors")
        for error in e.errors():
            # TODO: Display the source of the invalid setting (env/file/default?)
            loc = ".".join([str(value) for value in error["loc"]])
            err_console.print(f"\n[cyan]{loc}[/cyan]")
            err_console.print(f"\tInput: [red]{error['input']}[/red]")
            err_console.print(f"\t{error['msg']}")
        raise typer.Exit(1) from None


def process_model(model: Any, doc: TOMLDocument | Table | None = None, comments: bool = True) -> TOMLDocument | Table:
    if not isinstance(model, BaseModel):
        raise Exception

    if doc is None:
        doc = table()

    if comments:
        title = model.__class__.model_config.get("title")
        if title:
            doc.add(comment(title))
        if model.__class__.__doc__:
            for line in model.__class__.__doc__.split("\n"):
                doc.add(comment(line))

    for field, info in model.__class__.model_fields.items():
        value = getattr(model, field)

        if info.annotation and issubclass(info.annotation, BaseModel):
            nested_model = process_model(model=value, doc=None, comments=comments)
            doc.add(field, item(nested_model))
            continue

        if comments:
            doc.add(nl())
            if info.title:
                doc.add(comment(info.title))
            else:
                doc.add(comment(field))

            if info.description:
                doc.add(comment(info.description))

            if info.examples:
                if len(info.examples) > 1:
                    doc.add(comment("Examples:"))
                else:
                    doc.add(comment("Example:"))
                for example in info.examples:
                    doc.add(comment(f"{field} = {example}"))

            doc.add(comment("Default:"))
            doc.add(comment(f"{field} = {info.default!s}"))

        if isinstance(value, bool | int | float | str | list):
            doc.add(field, item(value))
        elif value is not None:
            doc.add(field, item(str(value)))
    return doc
