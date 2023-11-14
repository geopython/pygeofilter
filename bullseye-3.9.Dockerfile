FROM python:3.9-bullseye

LABEL description="Test executor"

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update --fix-missing \
  && apt-get install -y --no-install-recommends \
  binutils \
  libproj-dev \
  gdal-bin \
  libgdal-dev \
  libsqlite3-mod-spatialite \
  spatialite-bin \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY requirements-test.txt .
COPY requirements-dev.txt .
RUN pip install -r requirements-test.txt
RUN pip install -r requirements-dev.txt
RUN pip install pygdal=="`gdal-config --version`.*"

COPY pygeofilter pygeofilter
COPY tests tests
COPY README.md .
COPY setup.py .
RUN pip install -e .

CMD ["python", "-m", "pytest"]
