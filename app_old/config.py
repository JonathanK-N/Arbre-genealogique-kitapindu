import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("KITAPINDU_SECRET_KEY", "change-this-secret")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get(
            "KITAPINDU_DATABASE_URI",
            f"sqlite:///{(INSTANCE_DIR / 'kitapindu.db').as_posix()}",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_NAME = "kitapindu_session"
