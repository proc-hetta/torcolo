import io
import mimetypes
from uuid import uuid4

import magic
from sqlalchemy import select
from flask import (
    Flask,
    request,
    send_file,
    make_response,
)

from config import config
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
    return "OK"


@app.post(f"/files")
@authenticated
def post_file():
    file = request.files["file"]

    file_id = uuid4()
    with db.session() as s:
        s.add(
            File(
                id = file_id,
                filename = file.filename,
                data = file.stream.read(),
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
    file_content = file.data
    filename = str(file.id)
    mime_type = magic.from_buffer(file_content, mime=True)
    if (file_extension := mimetypes.guess_extension(mime_type)):
        filename += file_extension
    return send_file(
        io.BytesIO(file_content),
        mimetype=mime_type,
        as_attachment=True,
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
    with db.session() as s:
        s.delete(file)
        s.add(
            File(
                id = file.id,
                filename = file.filename,
                data = request.files["file"].stream.read(),
            )
        )
        s.commit()
    return {}, 204


@app.get(f"/files/manifest")
@authenticated
def get_files():
    with db.session() as s:
        entries = list(map(
            lambda row: {
                "id": str(row[0]),
                "filename": row[1],
                "last_modified": row[2].isoformat(),
            },
            s.execute(
                select(
                    File.id,
                    File.filename,
                    File.last_modified)
                .order_by(File.last_modified.desc()))
                .fetchall(),
        ))
    return {"entries": entries}
