import csv
import logging
import time
from abc import ABC, abstractmethod
from itertools import batched
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urljoin

import requests
from pydantic import ValidationError
from requests.models import HTTPError

from rockbox_listenbrainz_scrobbler.api_model import (
    MAX_LISTENS_PER_REQUEST,
    SubmitListens,
)
from rockbox_listenbrainz_scrobbler.exceptions import (
    InvalidAuthTokenException,
    InvalidSubmitListensPayloadException,
)
from rockbox_listenbrainz_scrobbler.model import ScrobblerEntry, SongRatingEnum


class AbstractScrobbler(ABC):
    @abstractmethod
    def scrobble(self, entry: ScrobblerEntry) -> None:
        """
        Scrobble the given song to your Endpoint
        """
        raise NotImplementedError()

    @abstractmethod
    def scrobble_multiple(self, entries: Iterable[ScrobblerEntry]) -> None:
        """
        Scrobble multiple songs to your Endpoint
        """
        raise NotImplementedError()


class ListenBrainzScrobbler(AbstractScrobbler):
    def __init__(
        self, auth_token: str, base_url="https://api.listenbrainz.org"
    ) -> None:
        super().__init__()

        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {"Authorization": "Token {0}".format(self.auth_token)}

    def scrobble(self, entry: ScrobblerEntry) -> None:
        return self.scrobble_multiple([entry])

    def scrobble_multiple(
        self,
        entries: Iterable[ScrobblerEntry],
        batchsize: int = MAX_LISTENS_PER_REQUEST,
    ) -> None:
        for batch in batched(entries, n=batchsize):
            current_batch = list(batch)

            try:
                api_request = SubmitListens.from_scrobbler_entries(current_batch)
                response = requests.post(
                    urljoin(self.base_url, "/1/submit-listens"),
                    json=api_request.model_dump(exclude_unset=True, exclude_none=True),
                    headers=self.headers,
                )
                if response.status_code != 200:
                    logging.error(
                        f"Could not submit listens. Reason: {response.json()}"
                    )

                if response.status_code == 401:
                    raise InvalidAuthTokenException("Invalid Auth Token.")
                elif response.status_code == 400:
                    raise InvalidSubmitListensPayloadException(
                        f"Invalid Payload: {response.json()}"
                    )
                elif response.status_code != 200:
                    raise HTTPError(response)

                remaining_calls = int(response.headers["X-RateLimit-Remaining"])
                ratelimit_reset = int(response.headers["X-RateLimit-Reset-In"])
                if remaining_calls == 0:
                    time.sleep(ratelimit_reset)

            except ValidationError as err:
                logging.error(
                    f"Payload too large. Trying smaller batchsize...\nReason: {err}"
                )
                if batchsize >= 2:
                    self.scrobble_multiple(current_batch, int(len(current_batch) / 2))


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
            print(row)
            scrobbles += [
                ScrobblerEntry(**{**row, **{"listening_from": listening_from}})
            ]
    return list(filter(lambda x: x.rating == SongRatingEnum.LISTENED, scrobbles))
