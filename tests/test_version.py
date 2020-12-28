from acru_l import __version__

import toml


def test_version():
    pyproject = toml.load("./pyproject.toml")
    version = pyproject['tool']['poetry']['version']
    assert __version__ == version
