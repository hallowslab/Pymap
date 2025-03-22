FROM debian:12.10 as debian-builder

# Install system and perl dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y git curl apt-file make time gcc lsb-release procps cpanminus \
    libauthen-ntlm-perl libcgi-pm-perl libcrypt-openssl-rsa-perl libdata-uniqid-perl libpar-packer-perl \
    libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl libio-socket-inet6-perl \
    libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl libtest-requires-perl \
    libparse-recdescent-perl libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libtest-mock-guard-perl \
    libsys-meminfo-perl libterm-readkey-perl libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl \
    libtest-nowarnings-perl libtest-deep-perl libtest-warn-perl libnet-server-perl libpackage-stash-perl libpackage-stash-xs-perl

# Clean apt
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Perl modules for imapsync
# See https://imapsync.lamiral.info/FAQ.d/FAQ.SSL_errors.txt
RUN cpanm Dist::CheckConflicts Module::Implementation IO::Socket::SSL

# Required for imapsync dependecy check
RUN apt-file update

# Clone and install imapsync
WORKDIR /opt/imapsync
RUN git clone https://github.com/imapsync/imapsync.git . && make install


FROM debian:12.10 as debian-base
# Needed for fixing permissions of files created by Docker:
ARG UID=1000 \
    GID=1000 \
    DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT \
    PYMAP_LOGDIR \
    SECRET_KEY \
    POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD

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
    # app:
    DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    STATIC_ROOT=${STATIC_ROOT} \
    PYMAP_LOGDIR=${PYMAP_LOGDIR} \
    SECRET_KEY=${SECRET_KEY} \
    POSTGRES_DB=${POSTGRES_DB} \
    POSTGRES_USER=${POSTGRES_USER} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD}


# Install app dependencies
RUN apt-get update && apt-get install --no-install-recommends -y redis nginx supervisor postgresql python3 pipx tmux
# Clean apt
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

COPY --from=debian-builder /usr/bin/imapsync /usr/bin/imapsync

# supervisor program users 
RUN adduser --system --home /var/lib/redis --no-create-home --shell /bin/false --group redis \
    && adduser pymap

# Create the log directory
RUN mkdir -p /var/log/pymap
RUN chown -R pymap:pymap /var/log/pymap

# Fix poetry directory permissions
RUN mkdir -p /opt/pypoetry
RUN chmod -R a+rx /opt/pypoetry

# Allow access to $STATIC_ROOT for nginx
RUN mkdir -p $STATIC_ROOT
RUN chown -R pymap:www-data $STATIC_ROOT

### BROKEN, database seems to startup can't run commands
# Switch to the postgres user to execute psql commands
#USER postgres

# Start the PostgreSQL service and create a database and user
#RUN /etc/init.d/postgresql start && \
#    psql --command "CREATE DATABASE $POSTGRES_DB;" > /var/log/postgresql/postgresql_setup.log 2>&1 && \
#    psql --command "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD' SUPERUSER CREATEDB CREATEROLE LOGIN;" >> /var/log/postgresql/postgresql_setup.log 2>&1 && \
#    psql --command "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;" >> /var/log/postgresql/postgresql_setup.log 2>&1
###

# Switch user
USER pymap
WORKDIR /home/pymap

# Create .pgpass file
RUN echo "localhost:5432:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > .pgpass
RUN chmod 600 .pgpass
# Create .pg_service.conf
# Didn't figure out why, but using printf to write to file seems to create issues establishing a connection on the django app
#RUN printf "[pymap]\nhost=localhost\nuser=$POSTGRES_USER\ndbname=$POSTGRES_DB\nport=5432\n" > .pg_service.conf
RUN echo "[pymap]\nhost=localhost\nuser=$POSTGRES_USER\ndbname=$POSTGRES_DB\nport=5432\n" > .pg_service.conf
# Add the secret key to the environment
RUN echo "export SECRET_KEY=$SECRET_KEY" >> /home/pymap/.bashrc
WORKDIR /home/pymap/app

# Install poetry
RUN pipx install poetry
# Add pipx executables to path
RUN pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/home/pymap/.local/bin:$PATH"

# Add poetry home to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy lock and project file for caching purposes
COPY ./src/poetry.lock /home/pymap/app/poetry.lock
COPY ./src/pyproject.toml /home/pymap/app/pyproject.toml


# Project initialization:
# RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
#   && poetry install \
#     $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
#     --no-interaction --no-ansi --sync

RUN poetry install $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
    --no-interaction --no-ansi --sync

# copy the app
COPY ./src /home/pymap/app/

# Create the log directory
RUN mkdir -p $PYMAP_LOGDIR

# Collect static assets
#RUN poetry run python manage.py collectstatic

# migrate (required for aio in first time setup)
# use --run-syncdb if this step becomes slow due to the amount of changes
#RUN poetry run python manage.py migrate --no-input
# Can't seem to connect before supervisor startup, so we use a init script
COPY Dockerfiles/aio/django_init.sh django_init.sh

# Switch to root for supervisor
USER root

# supervisor config
COPY templates/aio/supervisord.conf /etc/supervisor/supervisord.conf
# nginx config
COPY templates/aio/nginx.conf /etc/nginx/nginx.conf

# Handle tasks with supervisor
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
