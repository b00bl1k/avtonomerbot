FROM python:3.9

RUN apt update \
    && apt install -y nodejs \
    && pip install pipenv==2020.11.15

COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt \
    && pip install -r /tmp/requirements.txt

ADD avbot /app
WORKDIR /app
CMD ["./start.sh"]
