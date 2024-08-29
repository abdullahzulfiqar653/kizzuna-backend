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

python manage.py runserver 0.0.0.0:8000