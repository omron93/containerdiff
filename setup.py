#!/usr/bin/python3
#   ContainerDiff - tool to show differences among container images
#
#   Copyright (C) 2016 Marek Skalicky mskalick@redhat.com
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with containerdiff.  If not, see <http://www.gnu.org/licenses/>.
#

"""Suport for Python distributing."""

from setuptools import setup, find_packages

import containerdiff

# Get the long description from the README file
with open("README.rst", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name = "containerdiff",
    version = containerdiff.program_version,
    description = containerdiff.program_description,
    long_description=long_description,

    packages = find_packages(),
    package_data = {"containerdiff" : ["filter.json"]},

    install_requires=[
        "docker_py",
        "file-magic",
    ],

    author = "Marek Skalicky",
    author_email = "MSkalicky@seznam.cz",

    license = "GPL v3",
    keywords = "diff docker image",
    url = "https://github.com/omron93/ContainerDiffTool",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",

        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",

        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    scripts = ["bin/containerdiff"]
)

