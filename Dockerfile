###########
# BUILDER #
###########

# pull official base image
FROM python:3.11.4-slim-buster as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

# lint
RUN pip install --upgrade pip
RUN pip install flake8==6.0.0
COPY . /usr/src/app/
RUN flake8 --ignore=E501,F401,F811,E225,W503,W504 .

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

COPY ./config/logging_config.json ./config
#########
# FINAL #
#########

# pull official base image
FROM python:3.11.4-slim-buster

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
ENV APP_CONFIG=/home/app/web/config
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/config

WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
COPY --from=builder /usr/src/app/config/logging_config.json ./config
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*


# copy project
COPY . $APP_HOME
COPY ./config/logging_config.json $APP_CONFIG

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app
EXPOSE 8000/tcp
