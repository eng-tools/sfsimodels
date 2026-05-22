import subprocess
import pytest

about = {}
with open("sfsimodels/__about__.py") as fp:
    exec(fp.read(), about)

version = about['__version__']


def main():
    failures = pytest.main()
    if failures == 0:
        subprocess.check_call(["git", "tag", version, "-m", "version %s" % version])
        subprocess.check_call(["git", "push", "--tags", "origin", "master"])


if __name__ == "__main__":
    main()