#!/bin/bash

mkdir -p credentials
# To generate the content, do `cat google-credentials.json | base64`
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
    echo $GOOGLE_APPLICATION_CREDENTIALS_JSON | base64 -d > $GOOGLE_APPLICATION_CREDENTIALS
fi


if [ -n "$GOOGLE_CLIENT_SECRET_JSON" ]; then
    echo $GOOGLE_CLIENT_SECRET_JSON | base64 -d > $GOOGLE_CLIENT_SECRET_FILE
fi

python manage.py migrate

if [ -z "$1" ] || [ "$1" == "django" ]; then
    gunicorn cradarai.wsgi ${@:2}
elif [ "$1" == "celery-worker" ]; then
    celery -A cradarai worker -l info ${@:2}
elif [ "$1" == "celery-beat" ]; then
    celery -A cradarai beat -l info ${@:2}
else
    echo "Command not found"
fi