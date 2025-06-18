############################
# -- imapsync build stage --
############################
FROM debian:bookworm AS imap-builder

# Install system and perl dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y git curl apt-file make time gcc lsb-release procps cpanminus \
    libauthen-ntlm-perl libcgi-pm-perl libcrypt-openssl-rsa-perl libdata-uniqid-perl libpar-packer-perl \
    libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl libio-socket-inet6-perl \
    libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl libtest-requires-perl \
    libparse-recdescent-perl libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libtest-mock-guard-perl \
    libsys-meminfo-perl libterm-readkey-perl libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl \
    libtest-nowarnings-perl libtest-deep-perl libtest-warn-perl libnet-server-perl libpackage-stash-perl libpackage-stash-xs-perl libdigest-hmac-perl

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

############################
# ---- base stage ----
############################
FROM python:3.12-slim AS base

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    && pipx install poetry \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ARG DJANGO_ENV

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
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # Django
    DJANGO_ENV=${DJANGO_ENV} \
    # pipx
    # Set PATH to include pipx binary directory
    # ensurepath does not refresh the environment during the build it seems
    PATH="/root/.local/bin:$PATH"

# Change dir
WORKDIR /src

# Copy project dependency files
COPY src/pyproject.toml src/poetry.lock ./

# Install dependecies trough poetry
RUN poetry install $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
    --no-interaction --no-ansi --sync


############################
# ---- django stage ----
############################
FROM python:3.12-slim AS django

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ARG DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT \
    PYMAP_LOGDIR \
    PYMAP_HOSTNAME \
    PYMAP_ADMIN_USER \
    GROUPNAME \
    GID

# python:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # APP
    DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    STATIC_ROOT=${STATIC_ROOT} \
    PYMAP_HOSTNAME=${PYMAP_HOSTNAME}

# create user+group
RUN addgroup --gid $GID $GROUPNAME \
    && adduser --disabled-password --gecos '' --uid 1001 --gid $GID pymap

# Create the log directory and add permissions to user and group
RUN mkdir -p $PYMAP_LOGDIR
RUN touch "$PYMAP_LOGDIR/pymap-dev.log" "$PYMAP_LOGDIR/pymap.log"
RUN chown -R pymap:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR

# Copy init script
COPY Dockerfiles/base/django_init.sh /home/pymap/init.sh
# Copy the copy_secrets file
COPY Dockerfiles/base/copy_secrets.sh /home/pymap/copy_secrets.sh
RUN chmod +x /home/pymap/init.sh /home/pymap/copy_secrets.sh

# switch to user
USER pymap
WORKDIR /home/pymap/app

# copy virtualenv from build stage
COPY --from=base /src/.venv /home/pymap/app/.venv
ENV PATH="/home/pymap/app/.venv/bin:$PATH"

# Copy the code last to maximize layer caching
COPY src .

# fix perms
USER root
RUN chown -R pymap:pymap /home/pymap/app
USER pymap

ENTRYPOINT [ "/home/pymap/init.sh" ]
# CMD ["tail", "-f", "/dev/null"]

############################
# --- worker base stage ---
############################
FROM python:3.12-slim AS celery-worker

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# imapsync dependencies
RUN apt-get update && apt-get install --no-install-recommends -y libdigest-hmac-perl libencode-imaputf7-perl \
    libfile-copy-recursive-perl libio-socket-inet6-perl libwww-perl libdata-uniqid-perl libcgi-pm-perl \
    libio-socket-ssl-perl libio-tee-perl libmail-imapclient-perl libterm-readkey-perl libunicode-string-perl \
    libreadonly-perl libsys-meminfo-perl libregexp-common-perl libfile-tail-perl libtest-mockobject-perl \
    libjson-webtoken-perl liburi-perl libhtml-parser-perl libauthen-ntlm-perl \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
    
COPY --from=imap-builder /usr/bin/imapsync /usr/bin/imapsync

ARG DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT \
    PYMAP_LOGDIR \
    PYMAP_HOSTNAME \
    GROUPNAME \
    GID

# APP
ENV DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    STATIC_ROOT=${STATIC_ROOT} \
    PYMAP_HOSTNAME=${PYMAP_HOSTNAME}


# Create user and group
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID celery

# Create the log directory
RUN mkdir -p $PYMAP_LOGDIR
RUN touch "$PYMAP_LOGDIR/pymap-dev.log" "$PYMAP_LOGDIR/pymap.log"
RUN chown -R celery:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR

# Copy the copy_secrets file
COPY Dockerfiles/base/copy_secrets.sh /home/celery/copy_secrets.sh
RUN chmod +x /home/celery/copy_secrets.sh

# Switch to user and app directory
USER celery

WORKDIR /home/celery/app

# copy virtualenv from build stage
COPY --from=base /src/.venv /home/celery/app/.venv
ENV PATH="/home/celery/app/.venv/bin:$PATH"

# Copy the source code
COPY ./src/ ./

USER root
RUN chown -R celery:$GROUPNAME /home/celery/app/
USER celery

# celery -A pymap.celery worker -E --pool=gevent --statedb=celery/working.state"
CMD ["sh", "-c", "sleep 5 && $(poetry env info --path)/bin/celery -A pymap.celery worker -l INFO --concurrency=500 --pool=gevent"]