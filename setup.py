# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

"""Install pygeofilter."""

import os
import os.path

from setuptools import find_packages, setup

# don't install dependencies when building win readthedocs
on_rtd = os.environ.get("READTHEDOCS") == "True"

# use README.md for project long_description
with open("README.md") as f:
    readme = f.read()

description = (
    "pygeofilter is a pure Python parser implementation of OGC filtering standards"
)

setup(
    name="pygeofilter",
    description=description,
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Fabian Schindler",
    author_email="fabian.schindler@eox.at",
    url="https://github.com/geopython/pygeofilter",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=(
        [
            "click",
            "dateparser",
            "lark",
            "pygeoif>=1.0.0"
        ]
        if not on_rtd
        else []
    ),
    extras_require={
        "backend-django": ["django"],
        "backend-sqlalchemy": ["geoalchemy2", "sqlalchemy"],
        "backend-native": ["shapely"],
        "backend-elasticsearch": ["elasticsearch", "elasticsearch-dsl"],
        "backend-opensearch": ["opensearch-py", "opensearch-dsl"],
        "fes": ["pygml>=0.2"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    entry_points={
        'console_scripts': [
            'pygeofilter=pygeofilter.cli:cli'
        ]
    },
    tests_require=["pytest"]
)
