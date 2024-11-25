from enum import Enum
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class SongRatingEnum(str, Enum):
    LISTENED = "L"
    SKIPPED = "S"


class ScrobblerEntry(BaseModel):
    artist: str = Field(validation_alias=AliasChoices("artist", "#ARTIST"))
    album: str = Field(validation_alias=AliasChoices("album", "#ALBUM"))
    title: str = Field(validation_alias=AliasChoices("title", "#TITLE"))
    tracknum: int = Field(validation_alias=AliasChoices("tracknum", "#TRACKNUM"))
    length: int = Field(validation_alias=AliasChoices("length", "#LENGTH"))
    rating: SongRatingEnum = Field(validation_alias=AliasChoices("rating", "#RATING"))
    timestamp: int = Field(validation_alias=AliasChoices("timestamp", "#TIMESTAMP"))
    musicbrainz_trackid: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("musicbrainz_trackid", "#MUSICBRAINZ_TRACKID"),
    )
    listening_from: str = "rockbox"

    @field_validator("musicbrainz_trackid")
    @classmethod
    def ensure_empty_as_none(cls, value):
        if value is None:
            return value

        if len(value.strip()) == 0:
            return None

        return value
