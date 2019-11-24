FROM python:3.7

RUN apt-get update \
    && apt-get install -y nodejs \
    && pip install pipenv==2018.11.26

COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt

ADD avbot /app
WORKDIR /app
CMD ["python", "bot.py"]
