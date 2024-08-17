FROM python:3.10.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV WORKDIR=/usr/bot
ENV USER=padel
ENV APP_HOME=/home/bot/DiscordMatchmaker


RUN pip install --upgrade pip
RUN pip install pipenv

RUN apt-get update
RUN apt-get -y install nano

RUN adduser --system --group $USER
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY . $APP_HOME
USER $USER

RUN pipenv install