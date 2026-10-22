"""Local static server for the bundled WebGL user interface."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietStaticHandler(SimpleHTTPRequestHandler):
    """Serve frontend assets without writing one log line per browser request."""

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create the local server that hosts the bundled WebGL application."""
    web_root = Path(__file__).with_name("web")
    handler = partial(QuietStaticHandler, directory=str(web_root))
    return ThreadingHTTPServer((host, port), handler)
