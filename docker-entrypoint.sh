#!/bin/bash

python manage.py migrate

exec gunicorn cradarai.wsgi:application --bind 0.0.0.0:8000
