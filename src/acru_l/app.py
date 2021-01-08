#!/usr/bin/env python3
from acru_l.core import app_factory


def main():
    app = app_factory()
    app.synth()


if __name__ == "__main__":
    main()
