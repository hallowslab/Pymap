FROM python:3.11

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

ARG DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT \
    PYMAP_LOGDIR \
    PYMAP_ADMIN_USER \
    PYMAP_ADMIN_PASSWORD \
    POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD \
    POSTGRES_HOST \
    POSTGRES_PORT \
    GROUPNAME \
    GID

# python:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip:
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore \
    # poetry:
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # APP
    DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    STATIC_ROOT=${STATIC_ROOT} \
    PYMAP_HOSTNAME=${PYMAP_HOSTNAME}

# Create user and group
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID pymap

# Create the log directory and add permissions to user and group
RUN mkdir -p $PYMAP_LOGDIR
RUN touch "$PYMAP_LOGDIR/pymap-dev.log" "$PYMAP_LOGDIR/pymap.log"
RUN chown -R pymap:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR

USER pymap
WORKDIR /home/pymap/app

# Poetry install
RUN pipx install poetry \
    # Add pipx executables to path
    && pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/home/pymap/.local/bin:$PATH"
# Add poetry home to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Create .pg_service.conf
RUN cat > ~/.pg_service.conf <<EOF
[pymap]
host=$POSTGRES_HOST
user=$POSTGRES_USER
dbname=$POSTGRES_DB
port=$POSTGRES_PORT
EOF

# Create .pgpass file in the app directory so that it can be loaded by the app
RUN echo "$POSTGRES_HOST:$POSTGRES_PORT:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > ./.pgpass
RUN chmod 600 ./.pgpass

# Create .secret file for SECRET_KEY
#RUN echo "$SECRET_KEY" > ./.secret
# The secret file should be mounted at runtime
# create it and set permissions to avoid issues reading
RUN touch .secret
RUN chmod 600 .secret


# Copy the project files
COPY ./src/pyproject.toml ./
COPY ./src/poetry.lock ./

COPY Dockerfiles/django/init.sh /home/pymap/init.sh

# Install dependecies trough poetry
RUN poetry install $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
    --no-interaction --no-ansi --sync

# copy the app
COPY ./src ./

USER root
RUN chown -R pymap:pymap /home/pymap/app/
USER pymap

ENTRYPOINT [ "/home/pymap/init.sh" ]
# For debbuging
#CMD ["tail", "-f", "/dev/null"]