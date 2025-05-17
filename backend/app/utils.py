from typing import Literal
from unicodedata import normalize
from urllib.parse import quote

import humps
from fastapi.routing import APIRoute


def generate_unique_route_id(route: APIRoute) -> str:
    route_tag = humps.pascalize(str(route.tags[0]))
    route_name = humps.pascalize(route.name)
    return f"{route_tag}_{route_name}"


def content_disposition_header(filename: str, type: Literal["attachment", "inline"] = "attachment") -> str:
    """Build an appropriate value for a Content-Disposition HTTP header"""

    # normalize the filename to ascii only characters
    ascii = normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    header = f'{type}; filename="{ascii}"'

    # if the filename contained non-ascii characters, append the filename* parameter
    if ascii != filename:
        header += f"; filename*=UTF-8''{quote(filename)}"

    return header
