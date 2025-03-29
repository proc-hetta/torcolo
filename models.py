from uuid import UUID

from config import config
from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    AliasGenerator,
)
from pydantic.alias_generators import to_camel
from flask_pydantic_api import UploadedFile


class CamelCaseBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=to_camel,
        ),
        extra="forbid",
        serialize_by_alias=True,
    )


class PostFile(CamelCaseBaseModel):
    file: UploadedFile
    healthbar: Optional[int] = config.default_healthbar


class RequestManifest(CamelCaseBaseModel):
    older: Optional[bool] = False
    filename: Optional[str] = ""
    before: Optional[datetime] = datetime.max.isoformat()
    after: Optional[datetime] = datetime.min.isoformat()
    limit: Optional[int] = config.limit


class FileEntry(CamelCaseBaseModel):
    id: UUID
    filename: str
    last_modified: datetime
    remaining: Optional[int]


class Entries(CamelCaseBaseModel):
    entries : list[FileEntry]
