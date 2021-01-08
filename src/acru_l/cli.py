import os
import subprocess
import sys

from dotenv import load_dotenv


load_dotenv()


def main():
    dirname = os.path.dirname(__file__)
    process = subprocess.run(
        ["cdk", f"--app={os.path.join(dirname, 'app.py')}"] + sys.argv[1:]
    )
    sys.exit(process.returncode)
