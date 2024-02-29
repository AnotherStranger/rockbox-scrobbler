from enum import Enum

from pydantic import AliasChoices, BaseModel, Field


class SongRatingEnum(str, Enum):
    LISTENED: str = "L"
    SKIPPED: str = "S"


class ScrobblerEntry(BaseModel):
    artist: str = Field(validation_alias=AliasChoices("artist", "#ARTIST"))
    album: str = Field(validation_alias=AliasChoices("album", "#ALBUM"))
    title: str = Field(validation_alias=AliasChoices("title", "#TITLE"))
    tracknum: int = Field(validation_alias=AliasChoices("tracknum", "#TRACKNUM"))
    length: int = Field(validation_alias=AliasChoices("length", "#LENGTH"))
    rating: SongRatingEnum = Field(validation_alias=AliasChoices("rating", "#RATING"))
    timestamp: int = Field(validation_alias=AliasChoices("timestamp", "#TIMESTAMP"))
    musicbrainz_trackid: str = Field(
        validation_alias=AliasChoices("musicbrainz_trackid", "#MUSICBRAINZ_TRACKID")
    )
    listening_from: str = "rockbox"
