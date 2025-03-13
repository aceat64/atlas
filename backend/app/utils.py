from typing import Literal
from unicodedata import normalize
from urllib.parse import quote


def content_disposition_header(
    filename: str, type: Literal["attachment", "inline"] = "attachment"
) -> str:
    """Build an appropriate value for a Content-Disposition HTTP header"""

    # normalize the filename to ascii only characters
    ascii = normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    header = f'{type}; filename="{ascii}"'

    # if the filename contained non-ascii characters, append the filename* parameter
    if ascii != filename:
        header += f"; filename*=UTF-8''{quote(filename)}"

    return header
