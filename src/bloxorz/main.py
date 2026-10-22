"""Application entry point for the bundled WebGL UI."""

import threading
import webbrowser
import platform
import subprocess

from bloxorz.api_server import SolverHandler
from bloxorz.ui.web_server import create_server
from http.server import ThreadingHTTPServer


def open_browser(url: str) -> None:
    """Open the UI in Windows when the launcher is running inside WSL."""
    if "microsoft" in platform.release().lower():
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "", url])
            return
        except OSError:
            pass
    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error:
        pass


def main() -> None:
    """Start the WebGL frontend and Python solver API together."""
    try:
        api_server = ThreadingHTTPServer(("127.0.0.1", 8001), SolverHandler)
        web_server = create_server()
    except OSError as exc:
        raise RuntimeError(
            "Cannot start Bloxorz servers. Ports 8000 and 8001 may already be "
            "in use. Close the old Bloxorz process and try again."
        ) from exc
    api_thread = threading.Thread(target=api_server.serve_forever, daemon=True)
    web_thread = threading.Thread(target=web_server.serve_forever, daemon=True)
    api_thread.start()
    web_thread.start()

    url = "http://127.0.0.1:8000/index.html"
    print(f"Bloxorz WebGL UI: {url}")
    print("Python solver API: http://127.0.0.1:8001")
    print("Open this URL manually if the browser does not open:", url, flush=True)
    open_browser(url)
    try:
        api_thread.join()
    except KeyboardInterrupt:
        print("\nStopping Bloxorz UI...")
    finally:
        api_server.shutdown()
        web_server.shutdown()
        api_server.server_close()
        web_server.server_close()

if __name__ == "__main__":
    main()
