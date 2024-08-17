FROM python:3.10.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV APP_HOME=/DiscordMatchmaker


RUN pip install --upgrade pip
RUN pip install pipenv

RUN apt-get update
RUN apt-get -y install nano

WORKDIR $APP_HOME

COPY . $APP_HOME

RUN pipenv install