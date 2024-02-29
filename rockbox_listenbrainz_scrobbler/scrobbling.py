import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

from pylistenbrainz import Listen, ListenBrainz

from rockbox_listenbrainz_scrobbler.model import ScrobblerEntry, SongRatingEnum


class AbstractScrobbler(ABC):
    @abstractmethod
    def scrobble(self, entry: ScrobblerEntry) -> None:
        """
        Scrobble the given song to your Endpoint
        """
        raise NotImplementedError()

    @abstractmethod
    def scrobble_multiple(self, entry: Iterable[ScrobblerEntry]) -> None:
        """
        Scrobble multiple songs to your Endpoint
        """
        raise NotImplementedError()


class ListenBrainzScrobbler(AbstractScrobbler):
    def __init__(self, auth_token: str) -> None:
        super().__init__()

        self.client = ListenBrainz()
        self.client.set_auth_token(auth_token)

    def scrobble(self, entry: ScrobblerEntry) -> None:
        return self.scrobble_multiple([entry])

    def scrobble_multiple(self, entry: Iterable[ScrobblerEntry]) -> None:
        listens = [
            Listen(
                track_name=listen.title,
                artist_name=listen.artist,
                release_name=listen.album,
                listened_at=listen.timestamp,
                recording_mbid=listen.musicbrainz_trackid,
                listening_from=listen.listening_from,
            )
            for listen in entry
        ]

        self.client.submit_multiple_listens(listens)


def read_rockbox_log(
    rockbox_scrobbler_log_path: Path, listening_from: str = "rockbox"
) -> List[ScrobblerEntry]:
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
    return list(filter(lambda x: x.rating == SongRatingEnum.LISTENED, scrobbles))
