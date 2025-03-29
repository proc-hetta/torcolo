import io
import mimetypes
from uuid import uuid4
from datetime import datetime

import magic
from sqlalchemy import select
from flask import (
    Flask,
    request,
    send_file,
    make_response,
)

from config import (
    config,
    VERSION,
)
from utils import (
    inject_file,
    authenticated,
)
from db import (
    db,
    File
)

from flask_pydantic_api import pydantic_api
from models import (
    PostFile,
    RequestManifest,
    FileEntry,
    Entries
)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
app.logger.setLevel(config.log_level)
db.init_app(app)

with app.app_context():
    db.create_all()


@app.get(f"/")
def root():
    return {
        "major": VERSION.major,
        "minor": VERSION.minor,
        "micro": VERSION.micro,
        "complete": str(VERSION),
    }


@app.post(f"/files")
@authenticated
@pydantic_api(
    name= "/files",
    tags= ["files"],
)
def post_file(body: PostFile):
    if body.healthbar:
        healthbar = int(body.healthbar)
    file_id = uuid4()
    with db.session() as s:
        s.add(
            File(
                id = file_id,
                filename = body.file.filename,
                data = body.file.stream.read(),
                healthbar = body.healthbar,
            )
        )
        s.commit()

    response = make_response(
        {},
        201
    )
    response.location = f"/files/{str(file_id)}"
    return response


@app.get(f"/files/<uuid:file>")
@inject_file
def get_file(file):
    as_attachment = "download" in request.args
    use_original_name = "original_name" in request.args
    file_content = file.data
    filename = file.filename if use_original_name else str(file.id)
    mime_type = magic.from_buffer(file_content, mime=True)
    if not use_original_name and (file_extension := mimetypes.guess_extension(mime_type)):
        filename += file_extension
    filename = request.args.get('filename', filename)
    with db.session() as s:
        s_file = s.get(File, file.id)
        s_file.downloads += 1
        if s_file.healthbar is not None and s_file.downloads >= s_file.healthbar:
            s.delete(s_file)
        s.commit()
    return send_file(
        io.BytesIO(file_content),
        mimetype=mime_type,
        as_attachment=as_attachment,
        download_name=filename
    )


@app.delete(f"/files/<uuid:file>")
@authenticated
@inject_file
def delete_file(file):
    with db.session() as s:
        s.delete(file)
        s.commit()
    return {}, 204


@app.put(f"/files/<uuid:file>")
@authenticated
@inject_file
def put_file(file):
    # SQLAlchemy does not yet have a backend-agnostic upsert construct (https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-queryguide-upsert)
    # Update download counter
    with db.session() as s:
        s.delete(file)
        s.add(
            File(
                id = file.id,
                filename = file.filename,
                data = request.files["file"].stream.read(),
                healthbar = file.healthbar
            )
        )
        s.commit()
    return {}, 204


@app.get(f"/files/manifest")
@authenticated
@pydantic_api(
    name= "/files/manifest",
    tags= ["files"]
)
def get_files(manifest: RequestManifest):
    with db.session() as s:
        return Entries(entries = list(map(
            lambda row: FileEntry(
                id=row[0],
                filename=row[1],
                last_modified=row[2],
                remaining=row[3]),
            s.execute(
                select(
                    File.id,
                    File.filename,
                    File.last_modified,
                    File.healthbar - File.downloads)
                .where(File.filename.ilike(f"%{manifest.filename}%"))
                .where(File.last_modified.between(manifest.after, manifest.before))
                .order_by(File.last_modified.asc() if manifest.older else File.last_modified.desc())
                .limit(manifest.limit)
            ).fetchall()
        )))