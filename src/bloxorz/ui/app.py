"""Compatibility entry point for the bundled WebGL UI."""


class BloxorzApp:
    """Launch the same WebGL application used by ``bloxorz.main``."""

    def run(self) -> None:
        from bloxorz.main import main

        main()
