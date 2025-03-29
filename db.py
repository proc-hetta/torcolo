from uuid import UUID
from datetime import datetime

from typing import Optional
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import (
    Integer,
    LargeBinary,
    DateTime,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from config import config


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True)
    filename: Mapped[str] = mapped_column(String())
    data: Mapped[bytes] = mapped_column(LargeBinary())
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    downloads: Mapped[int] = mapped_column(
        Integer(),
        server_default = "0",
    )
    healthbar: Mapped[Optional[int]] = mapped_column(Integer())

db = SQLAlchemy(model_class=Base)
