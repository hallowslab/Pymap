FROM python:3.11

WORKDIR /app
RUN set -xe

# Poetry install
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry --version

# copy the app
COPY ./src /app/

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "poetry shell && celery -A pymap.celery worker -l INFO"]
