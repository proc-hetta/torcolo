import io
import hashlib
import mimetypes

import magic
from sqlalchemy import select
from flask import (
    Flask,
    request,
    send_file,
    make_response,
)
from pydantic import ValidationError
from flask_pydantic_api import pydantic_api

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
from models import (
    PostFile,
    GetManifestRequest,
    GetManifestResponse,
    GetManifestResponseEntry,
)

from alembic.config import Config
from alembic.command import ( check, upgrade, current )
from alembic.util.exc import CommandError

# migration hook
alembic_cfg = Config(config.alembic_path)
try:
    check(alembic_cfg)
except CommandError as err:
    upgrade(alembic_cfg, "head")
finally:
    current(alembic_cfg)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
app.logger.setLevel(config.log_level)
db.init_app(app)


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return {}, 422


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
    data = body.file.stream.read()
    file_id = hashlib.sha256(data).hexdigest()
    with db.session() as s:
        s.add(
            File(
                id = file_id,
                filename = body.file.filename,
                data = data,
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


@app.get(f"/files/<string:file>")
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


@app.delete(f"/files/<string:file>")
@authenticated
@inject_file
def delete_file(file):
    with db.session() as s:
        s.delete(file)
        s.commit()
    return {}, 204


@app.put(f"/files/<string:file>")
@authenticated
@inject_file
@pydantic_api(
    name="/files/{fileId}",
    tags=["files"]
)
def put_file(file, new_file: PostFile):
    # SQLAlchemy does not yet have a backend-agnostic upsert construct (https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-queryguide-upsert)
    # Update download counter
    with db.session() as s:
        s.delete(file)
        s.add(
            File(
                id = file.id,
                filename = new_file.file.filename,
                data = new_file.file.stream.read(),
                healthbar = new_file.healthbar,
                downloads = 0,
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
def get_manifest(manifest: GetManifestRequest):
    with db.session() as s:
        return GetManifestResponse(entries = list(map(
            lambda row: GetManifestResponseEntry(
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
