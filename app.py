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
def post_file():
    file = request.files["file"]
    hp = request.files.get("n_downloads", config.healthbar)
    file_id = uuid4()
    with db.session() as s:
        s.add(
            File(
                id = file_id,
                filename = file.filename,
                data = file.stream.read(),
                n_downloads = hp
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
    file_content = file.data
    filename = str(file.id)
    mime_type = magic.from_buffer(file_content, mime=True)
    if (file_extension := mimetypes.guess_extension(mime_type)):
        filename += file_extension
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
        if file.n_downloads < file.healthbar:
            s.add(
                File(
                    id = file.id,
                    filename = file.filename,
                    data = request.files["file"].stream.read(),
                    n_downloads = file.n_downloads + 1,
                    healthbar = file.healthbar
                )
            )
        s.commit()
    return {}, 204


@app.get(f"/files/manifest")
@authenticated
def get_files():
    older = "older" in request.args
    filename = f"%{request.args.get('filename', '')}%"
    before = datetime.fromisoformat(request.args.get("before", datetime.now().isoformat()))
    after = datetime.fromisoformat(request.args.get("after", datetime.min.isoformat()))
    limit = int(request.args.get("limit", 100))

    with db.session() as s:
        entries = list(map(
            lambda row: {
                "id": row[0],
                "filename": row[1],
                "last_modified": row[2].isoformat(),
            },
            s.execute(
                select(
                    File.id,
                    File.filename,
                    File.last_modified)
                .where(File.filename.ilike(filename))
                .where(File.last_modified.between(after, before))
                .order_by(File.last_modified.asc() if older else File.last_modified.desc())
                .limit(limit)
            ).fetchall()
        ))

    return {"entries": entries}
