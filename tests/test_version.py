from acru_l import __version__

import toml

from acru_l.utils import traverse


def test_version():
    pyproject = toml.load("./pyproject.toml")
    version = traverse(pyproject, "tool.poetry.version")
    assert __version__ == version
