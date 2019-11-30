FROM python:3.7-alpine

RUN apk --update --no-cache add gcc musl-dev libffi-dev python3-dev \
    postgresql-dev nodejs \
    && pip install pipenv==2018.11.26

COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt

ADD avbot /app
WORKDIR /app
CMD ["python", "bot.py"]
