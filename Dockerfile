FROM python:3.10.14-slim

ENV APP_HOME=/home/DiscordMatchmaker


RUN pip install --upgrade pip
RUN pip install pipenv

RUN apt-get update
RUN apt-get -y install --no-install-recommends \
    nano \
    libglx-mesa0 \
    libgl1 \
    libglib2.0-0

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY ./Pipfile.lock $APP_HOME/Pipfile.lock
COPY ./Pipfile $APP_HOME/Pipfile

COPY api $APP_HOME/api
COPY bot $APP_HOME/bot
COPY clients $APP_HOME/clients

RUN pipenv install