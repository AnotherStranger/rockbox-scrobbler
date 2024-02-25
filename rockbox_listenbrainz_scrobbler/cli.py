import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

import rockbox_listenbrainz_scrobbler
from rockbox_listenbrainz_scrobbler import rockbox_listenbrainz_ui
from rockbox_listenbrainz_scrobbler.scrobbling import (
    ListenBrainzScrobbler,
    read_rockbox_log,
)

app = typer.Typer()


@app.command()
def upload_rockbox(
    rockbox_scrobbler_log_path: Annotated[
        Path, typer.Argument(help="Path to the .scrobbler.log file.")
    ],
    auth_token: Annotated[
        str,
        typer.Option(
            prompt="Please provide your Listenbrainz Token (input hidden)",
            hide_input=True,
        ),
    ],
    listening_from: Annotated[
        str, typer.Option(help="Name of the app. You can choose any name here.")
    ] = "rockbox",
):
    """
    Uploads a .scrobbler.log file to Listenbrainz
    """
    scrobbles = read_rockbox_log(rockbox_scrobbler_log_path, listening_from)
    client = ListenBrainzScrobbler(auth_token)
    client.scrobble_multiple(scrobbles)


@app.command()
def launch_ui():
    """
    Launches a simple PyQt app for Scrobbling
    """
    sys.exit(rockbox_listenbrainz_ui.launch())


@app.command()
def version():
    """
    Prints the version of this tool and exits
    """
    print(f"v{rockbox_listenbrainz_scrobbler.__version__}")


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
