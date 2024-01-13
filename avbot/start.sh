#!/usr/bin/env bash

alembic upgrade head
python -m avbot.bot
