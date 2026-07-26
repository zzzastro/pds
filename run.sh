#!/usr/bin/env bash
set -e

VENV_SRC=/tmp/pds_venv

if [ ! -d "$VENV_SRC" ]; then
    python3 -m venv "$VENV_SRC"
    "$VENV_SRC/bin/pip" install -r requirements/base.txt
fi

if [ ! -L venv ] || [ "$(readlink venv)" != "$VENV_SRC" ]; then
    ln -sfn "$VENV_SRC" venv
fi

if [ ! -d venv/nltk_data ]; then
    ln -sfn "$PWD/nltk_data" venv/nltk_data
fi

venv/bin/python manage.py migrate
venv/bin/python manage.py runserver 0.0.0.0:8000
