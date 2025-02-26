from collections.abc import Callable
from enum import Enum
from typing import List, Optional, Set, TypeVar

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

T = TypeVar("T", bound=BaseModel)


def validate_max_size(max_size) -> Callable[[T], T]:
    def validator(model: T):
        json_data = model.model_dump_json().encode(encoding="utf8")
        if len(json_data) > max_size:
            raise ValueError(
                f"The payload is too large. Size: {len(json_data)} Bytes. Allowed: {max_size}"
            )
        return model

    return validator


def ensure_empty_as_none(value):
    if value is None:
        return value

    if len(value.strip()) == 0:
        return None

    return value


StringValidator = Annotated[Optional[str], ensure_empty_as_none]
PayloadValidator = Annotated[
    "ListenPayload", validate_max_size(MAX_LISTEN_PAYLOAD_SIZE)
]


class ListenType(str, Enum):
    SINGLE = "single"
    PLAYING_NOW = "playing_now"
    IMPORT = "import"


class AdditionalInfo(BaseModel):
    artist_mbids: Optional[List[str]] = None
    release_group_mbid: StringValidator = None
    release_mbid: StringValidator = None
    recording_mbid: StringValidator = None
    track_mbid: StringValidator = None
    work_mbids: Optional[List[str]] = None
    tracknumber: Optional[int] = None
    isrc: StringValidator = None
    spotify_id: StringValidator = None
    tags: Optional[Set[str]] = None
    media_player: StringValidator = "Rockbox"
    media_player_version: StringValidator = None
    submission_client: StringValidator = "Rockbox Scrobbler"
    submission_client_version: StringValidator = __version__
    music_service: StringValidator = None
    music_service_name: StringValidator = None
    origin_url: StringValidator = None
    duration_ms: Optional[int] = None
    duration: Optional[int] = None


class TrackMetadata(BaseModel):
    artist_name: str
    track_name: str
    release_name: StringValidator = None
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
