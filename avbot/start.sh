#!/usr/bin/env bash

alembic -c avbot/alembic.ini upgrade head
python -m avbot.bot
