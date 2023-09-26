#!/bin/bash
python manage.py migrate

# Please use with care (non-prod)
# python manage.py flush
python manage.py seed_database

python manage.py runserver 0.0.0.0:8000