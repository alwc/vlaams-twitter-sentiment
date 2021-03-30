"""Setup module for this Python package."""

import os
import re

from setuptools import find_packages, setup

# Fill `install_requires` with packages in environment.run.yml.
install_requires = []
with open(os.path.join(os.path.dirname(__file__), "environment.run.yml")) as spec:
    for line in spec:
        match = re.search(r"^\s*-\s+(?P<n>.+?)(?P<v>(?:~=|==|!=|<=|>=|<|>|===)[^\s\n\r]+)", line)
        if match and match.group("n") not in ("pip", "python"):
            install_requires.append(match.group("n") + match.group("v"))

setup(
    name="sentiment_flanders",
    version="0.0.0",
    description="A Python package that predicts the sentiment of Flemish Tweets.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=install_requires,
)
