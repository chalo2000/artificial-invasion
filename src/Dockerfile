FROM python:3.8-slim-buster

RUN mkdir usr/app
WORKDIR usr/app

COPY . .
RUN pip install -r requirements.txt
CMD sh start_server.sh