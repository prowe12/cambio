FROM python:3.10

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .

# install dependencies
RUN pip install poetry
RUN poetry config virtualenvs.create false \
    && poetry install

# Use when the css is in a separate file (using whitenoise)
RUN poetry run python manage.py collectstatic --noinput

EXPOSE 8000

# This command is good for just getting it running. This will run the server on port 8000
# CMD ["poetry", "run", "python", "manage.py", "runserver"]
# CMD ["poetry", "run", "python", "-m", "gunicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

# replace demo.wsgi with <project_name>.wsgi
CMD ["poetry", "run", "gunicorn", "--bind", ":8000", "--workers", "2", "cambio_site.wsgi"]

