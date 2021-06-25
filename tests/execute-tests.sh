#!/bin/sh

set -e

python -m pytest
cd tests/django_test
python manage.py test testapp
cd ../sqlalchemy_test/
python3 -m unittest