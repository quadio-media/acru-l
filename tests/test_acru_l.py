import os

from acru_l.core import app_factory


os.environ.setdefault("FOO", "bar")


def test_acru_l():
    app = app_factory()
    app.synth()
