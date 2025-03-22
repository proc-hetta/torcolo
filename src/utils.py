from functools import wraps
from flask import (
    request,
    current_app,
)

from db import (
    db,
    File,
)
from config import config


def authenticated(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with current_app.app_context():
            if request.authorization is None:
                return {}, 401
            if request.authorization.type.casefold() != "bearer" or request.authorization.token != config.token:
                return {}, 401
        return f(*args, **kwargs)
    return wrapper


def inject_file(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with current_app.app_context():
            file_id = request.view_args["file"]
        with db.session() as s:
            file = s.get(File, file_id)
            if not file:
                return {}, 404
            kwargs["file"] = file
        return f(*args, **kwargs)
    return wrapper
