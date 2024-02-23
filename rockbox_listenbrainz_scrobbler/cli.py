import sys
from pathlib import Path

import typer
from PySide6 import QtWidgets
from typing_extensions import Annotated

from rockbox_listenbrainz_scrobbler.scrobbling import (
    ListenBrainzScrobbler,
    read_rockbox_log,
)
from rockbox_listenbrainz_scrobbler.ui import ListenbrainzWidget

app = typer.Typer()


@app.command()
def upload_rockbox(
    rockbox_scrobbler_log_path: Path,
    auth_token: Annotated[
        str,
        typer.Option(
            prompt="Please provide your listenbrainz Token (input hidden)",
            hide_input=True,
        ),
    ],
    listening_from: Annotated[str, typer.Option()] = "rockbox",
):
    scrobbles = read_rockbox_log(rockbox_scrobbler_log_path, listening_from)
    client = ListenBrainzScrobbler(auth_token)
    client.scrobble_multiple(scrobbles)


@app.command()
def launch_ui():
    qt_app = QtWidgets.QApplication([])
    widget = ListenbrainzWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(qt_app.exec())


def main():
    """
    function entrypoint for tools.poetry.scripts
    """
    app()


if __name__ == "__main__":
    """
    entrypoint for running this script using python
    """
    main()
