import csv
from pathlib import Path

import pylistenbrainz
import typer
from typing_extensions import Annotated

from rockbox_listenbrainz_scrobbler.model import ScrobblerEntry

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
            scrobbles += [ScrobblerEntry(**row)]

    listens = [
        pylistenbrainz.Listen(
            track_name=listen.title,
            artist_name=listen.artist,
            release_name=listen.album,
            listened_at=listen.timestamp,
            recording_mbid=listen.musicbrainz_trackid,
            listening_from=listening_from,
        )
        for listen in scrobbles
    ]

    client = pylistenbrainz.ListenBrainz()
    client.set_auth_token(auth_token)

    client.submit_multiple_listens(listens)


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
