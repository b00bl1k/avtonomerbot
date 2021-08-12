#!/usr/bin/env bash

alembic upgrade head

python ./bot.py
