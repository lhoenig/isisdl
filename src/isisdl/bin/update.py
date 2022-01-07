#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import requests

from isisdl.settings import is_windows
from isisdl.backend.utils import logger, config_helper
from isisdl.version import __version__


def check_pypi_for_version() -> str:
    # Inspired from https://pypi.org/project/pypi-search

    to_search = requests.get("https://pypi.org/project/isisdl/").text
    version = re.search("<h1 class=\"package-header__name\">\n *(.*)?\n *</h1>", to_search)
    assert version is not None
    groups = version.groups()
    assert groups is not None
    assert len(groups) == 1

    return version[0].split()[1]


def check_github_for_version() -> str:
    res = requests.get("https://raw.githubusercontent.com/Emily3403/isisdl/main/src/isisdl/version.py")
    if not res.ok:
        logger.error("I could not obtain the latest version. Probably the link, which is hard-coded, is wrong.")
        assert False

    version = re.match("__version__ = \"(.*)?\"", res.text)
    if version is None:
        logger.error("I could not parse the specified version.")
        assert False

    return version.group(1)


def main() -> None:
    version_github = check_github_for_version()
    version_pypi = check_pypi_for_version()

    update_policy = config_helper.get_update_policy()
    update_policy = "2"
    if update_policy == "0":
        return

    if version_github > __version__:
        print(f"\nThere is a new version available: {version_github} (current: {__version__}).")
        if version_pypi == version_github:
            print("You're in luck: The new version is already available on PyPI.\n")
        else:
            print("Unfortunately the new version is not uploaded to PyPI yet.\n")

        if update_policy == "1":
            print("To install the new version type the following into your favorite shell!\n")
            if not is_windows:
                print("cd /tmp")

            if version_pypi == version_github:
                print("pip install --upgrade isisdl")
            else:
                print("git clone https://github.com/Emily3403/isisdl")
                print("pip install ./isisdl")

            return

        if update_policy == "2":
            if version_pypi == version_github:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "isisdl"])
            else:
                old_dir = os.getcwd()
                with TemporaryDirectory() as tmp:
                    os.chdir(tmp)
                    print(f"Cloning the repository into {tmp} ...")
                    ret = subprocess.check_call(["git", "clone", "https://github.com/Emily3403/isisdl"])
                    if ret:
                        print(f"Cloning failed with exit code {ret}")
                        return

                    print("Installing with pip ...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "./isisdl"])
                    os.chdir(old_dir)


if __name__ == '__main__':
    main()