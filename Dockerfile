FROM python:3.10

RUN apt update \
    && apt install -y nodejs \
    && pip install pipenv==2020.11.15 \
    && groupadd -r app \
    && useradd -r -g app app

COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt

ADD avbot /app
WORKDIR /app
USER app
CMD ["./start.sh"]
