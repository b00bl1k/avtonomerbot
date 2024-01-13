FROM python:3.11

RUN apt update \
    && apt install -y nodejs \
    && pip install pipenv==2023.6.2 \
    && groupadd -r app \
    && useradd -r -g app app

COPY Pipfile* /tmp/
RUN cd /tmp && pipenv requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt

ADD avbot /app/avbot
WORKDIR /app
RUN pybabel compile -d avbot/locale -D avbot

USER app
CMD ["avbot/start.sh"]
