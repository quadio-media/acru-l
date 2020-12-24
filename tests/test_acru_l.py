import os

from acru_l.apps.base import setup_app

os.environ.setdefault("AWS_ACCOUNT_ID", "fake")
os.environ.setdefault("AWS_REGION", "fake")
os.environ.setdefault("COMMIT_SHA", "fake")


def test_acru_l():
    app = setup_app()
    app.synth()
