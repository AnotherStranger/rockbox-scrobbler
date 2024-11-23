from collections.abc import Callable
from enum import Enum
from typing import List, Optional, Set

from pydantic import BaseModel, model_validator
from typing_extensions import Annotated

from rockbox_listenbrainz_scrobbler import __version__
from rockbox_listenbrainz_scrobbler.model import ScrobblerEntry

# Relevant listenbrainz Constants

# The maximum number of listens in a request.
MAX_LISTENS_PER_REQUEST = 1000

# Maximum overall listen size in bytes, to prevent egregious spamming.
MAX_LISTEN_SIZE = 10240

# The maximum size of a payload in bytes. The same as MAX_LISTEN_SIZE * MAX_LISTENS_PER_REQUEST.
MAX_LISTEN_PAYLOAD_SIZE = MAX_LISTENS_PER_REQUEST * MAX_LISTEN_SIZE

# The maximum number of tags per listen.
MAX_TAGS_PER_LISTEN = 50

# The maximum length of a tag
MAX_TAG_SIZE = 64

# The minimum acceptable value for listened_at field
LISTEN_MINIMUM_TS = 1033430400


def validate_max_size[T: BaseModel](max_size) -> Callable[[T], T]:
    def validator(model: T):
        json_data = model.model_dump_json().encode(encoding="utf8")
        if len(json_data) > max_size:
            raise ValueError(
                f"The payload is too large. Size: {len(json_data)} Bytes. Allowed: {max_size}"
            )
        return model

    return validator


PayloadValidator = Annotated[
    "ListenPayload", validate_max_size(MAX_LISTEN_PAYLOAD_SIZE)
]


class ListenType(str, Enum):
    SINGLE = "single"
    PLAYING_NOW = "playing_now"
    IMPORT = "import"


class AdditionalInfo(BaseModel):
    artist_mbids: Optional[List[str]] = None
    release_group_mbid: Optional[str] = None
    release_mbid: Optional[str] = None
    recording_mbid: Optional[str] = None
    track_mbid: Optional[str] = None
    work_mbids: Optional[List[str]] = None
    tracknumber: Optional[int] = None
    isrc: Optional[str] = None
    spotify_id: Optional[str] = None
    tags: Optional[Set[str]] = None
    media_player: Optional[str] = "Rockbox"
    media_player_version: Optional[str] = None
    submission_client: Optional[str] = "Rockbox Scrobbler"
    submission_client_version: Optional[str] = __version__
    music_service: Optional[str] = None
    music_service_name: Optional[str] = None
    origin_url: Optional[str] = None
    duration_ms: Optional[int] = None
    duration: Optional[int] = None


class TrackMetadata(BaseModel):
    artist_name: str
    track_name: str
    release_name: Optional[str] = None
    additional_info: Optional[AdditionalInfo] = None


class ListenPayload(BaseModel):
    track_metadata: TrackMetadata
    listened_at: Optional[int] = None

    @classmethod
    def from_rockbox_listen(cls, listen: ScrobblerEntry) -> "ListenPayload":
        return cls(
            listened_at=listen.timestamp,
            track_metadata=TrackMetadata(
                artist_name=listen.artist,
                release_name=listen.album,
                track_name=listen.title,
                additional_info=AdditionalInfo(
                    tracknumber=listen.tracknum,
                    duration=listen.length,
                    track_mbid=listen.musicbrainz_trackid,
                ),
            ),
        )


class SubmitListens(BaseModel):
    listen_type: ListenType
    payload: List[PayloadValidator]

    @classmethod
    def from_scrobbler_entries(cls, entries: List[ScrobblerEntry]) -> "SubmitListens":
        listen_type = ListenType.SINGLE if len(entries) == 1 else ListenType.IMPORT
        payloads = [ListenPayload.from_rockbox_listen(entry) for entry in entries]
        return cls(listen_type=listen_type, payload=payloads)

    @model_validator(mode="after")
    def validate_payload_size(self):
        total_size = sum(len(p.model_dump_json()) for p in self.payload)
        if total_size > MAX_LISTEN_PAYLOAD_SIZE:
            raise ValueError(
                f"The payload is too large. Size: {total_size} Bytes. Allowed: {MAX_LISTEN_PAYLOAD_SIZE}"
            )
        return self
