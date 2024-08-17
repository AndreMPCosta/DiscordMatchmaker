from functools import lru_cache
from logging import warning
from os import getenv
from tempfile import NamedTemporaryFile


class Secrets:
    def __init__(self):
        self.cert_file = getenv("CERT_FILE")
        self.key_file = getenv("KEY_FILE")

    @property
    def cert_file_path(self) -> str | None:
        if self.cert_file is not None:
            file = NamedTemporaryFile("w", delete=False)
            with file as f:
                f.write(self.cert_file)
            return file.name
        else:
            warning("No cert_file provided, switching to HTTP")
            return None

    @property
    def key_file_path(self) -> str | None:
        if self.key_file is not None:
            file = NamedTemporaryFile("w", delete=False)
            with file as f:
                f.write(self.key_file)
            return file.name
        else:
            warning("No key_file provided, switching to HTTP")
            return None


@lru_cache
def get_secrets() -> Secrets:
    return Secrets()
