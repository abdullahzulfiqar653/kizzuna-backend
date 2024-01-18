# cradar.ai

## Dependencies
For opening and saving non-wav files – like mp3 – you'll need ffmpeg or libav.

# To build and run

## In local
1. Install necessary packages, such as:
    - pipenv
    - mysql client
    - ffmpeg
2. Have the postgres database connection ready
3. Have the redis connection ready
4. Copy the content of .env.example to .env
5. Replace the following fields:
    - `OPENAI_API_KEY`
    - `GOOGLE_APPLICATION_CREDENTIALS`
    - `MASTER_DB_*`
    - `CELERY_BROKER_URL`
    - `EMAIL_HOST_USER` - Use gmail account
    - `EMAIL_HOST_PASSWORD` - **NOT** gmail account password. Please follow the [guideline](https://support.google.com/mail/answer/185833?hl=en) to create the app password and add it here.
6. Install the python dependencies - `pipenv install`
7. Go into the python virtual environment - `pipenv shell`
8. Migrate the database - `python manage.py migrate`
9.  Start the server - `python manage.py runserver`
10. Start the celery beat for scheduled tasks - `celery -A cradarai beat`
11. Start the celery worker for scheduled and async tasks - `celery -A cradarai worker`

## Using local docker
```shell
docker compose --profile local up
```
This `local` profile will run frontend, nginx and db also.


# Adding new python packages
1. Determine if the new package is only for local or need to push to server
    1. For local only, run `pipenv install --dev <package-name>`
    2. To install in server, run `pipenv install <package-name>`
2. Check Pipfile to see if the installation is as per intended. 
3. Fix the package version if possible to avoid version drift.
4. Generate the requirements.txt file `pipenv requirements > requirements.txt`

Note: In the server, python packages are installed from requirements.txt file rather than the pipenv because the versions are still drifting everytime we run `pipenv install`. So the step to generate the requirements.txt is really important for the server to install the new package. 


# Celery
The cronjob is defined in cradarai/celery.py.

1. To run celery worker:
    ```shell
    celery -A cradarai worker
    ```
    Restart the celery worker if the celery task functions are updated.

2. To run celery beat (the process to queue the cronjob):
    ```shell
    celery -A cradarai beat
    ```
    Restart the celery beat if the schedules are updated.

3. To run flower to monitor the celery workers:
    ```shell
    celery -A cradarai flower
    ```
    After that, go to localhost:5555.
