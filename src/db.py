from uuid import UUID
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import (
    LargeBinary,
    DateTime,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary())
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


db = SQLAlchemy(model_class=Base)
