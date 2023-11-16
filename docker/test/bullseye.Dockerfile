FROM python:3.10-bullseye
# finally there will be python version 3.9, 3.10 to run matrix tests with tox

LABEL description="Test executor"


RUN set -x \
    && pythonVersions='python3.9 python3.9-dev' \
    && apt-get update \
    && apt-get install -y --no-install-recommends  \ 
    # diverse python versions
    software-properties-common gpg-agent\
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get purge -y --autoremove software-properties-common gpg-agent  \
    && apt-get install -y --no-install-recommends $pythonVersions \
    # Project os dependencies
    && apt-get install -y --no-install-recommends \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    libsqlite3-mod-spatialite \
    spatialite-bin \ 
    # cleanup
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY requirements-test.txt requirements-base.txt README.md setup.py tox.ini ./

# Code base will binded by docker compose. Otherwise the container needs to rebuild on any code change.

# create dynamic requirements file with the current os gdal version
RUN echo "gdal==`gdal-config --version`.*" >> requirements-gdal.txt \
    && pip install tox

