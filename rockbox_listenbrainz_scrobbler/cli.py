import csv
from pathlib import Path

import pylistenbrainz
import typer
from typing_extensions import Annotated

from rockbox_listenbrainz_scrobbler.model import ScrobblerEntry
from rockbox_listenbrainz_scrobbler.scrobbling import ListenBrainzScrobbler

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
    scrobbles = []
    with rockbox_scrobbler_log_path.open(
        "r",
        encoding="utf8",
        newline="",
    ) as fp_scrobbler:
        for _ in range(4):  # skip header
            fp_scrobbler.readline()
        reader = csv.DictReader(
            fp_scrobbler,
            delimiter="\t",
            fieldnames=[
                "#ARTIST",
                "#ALBUM",
                "#TITLE",
                "#TRACKNUM",
                "#LENGTH",
                "#RATING",
                "#TIMESTAMP",
                "#MUSICBRAINZ_TRACKID",
            ],
        )
        for row in reader:
            scrobbles += [
                ScrobblerEntry(**{**row, **{"listening_from": listening_from}})
            ]

    client = ListenBrainzScrobbler(auth_token)
    client.scrobble_multiple(scrobbles)


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
