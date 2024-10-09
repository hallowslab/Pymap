FROM debian:bookworm AS debian-builder

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

FROM python:3.11

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# pipx install
RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    # imapsync dependencies
    libdigest-hmac-perl libencode-imaputf7-perl libfile-copy-recursive-perl libio-socket-inet6-perl libwww-perl \
    libio-socket-ssl-perl libio-tee-perl libmail-imapclient-perl libterm-readkey-perl libunicode-string-perl \
    libreadonly-perl libsys-meminfo-perl libregexp-common-perl libfile-tail-perl libtest-mockobject-perl \
    libjson-webtoken-perl liburi-perl libhtml-parser-perl libauthen-ntlm-perl libdata-uniqid-perl libcgi-pm-perl \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
    
COPY --from=debian-builder /usr/bin/imapsync /usr/bin/imapsync

ARG POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD \
    POSTGRES_HOST \
    POSTGRES_PORT \
    DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    PYMAP_LOGDIR \
    GROUPNAME \
    GID

ENV DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}


# Create user and group
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID celery

# Create the log directory
RUN mkdir -p $PYMAP_LOGDIR
RUN touch "$PYMAP_LOGDIR/pymap-dev.log" "$PYMAP_LOGDIR/pymap.log"
RUN chown -R celery:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR


# Switch to user and app directory
USER celery

WORKDIR /home/celery/app

# Poetry install
RUN pipx install poetry \
    # Add pipx executables to path
    && pipx ensurepath


# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/home/celery/.local/bin:$PATH"

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

# The secret file should be mounted at runtime
# create it and set permissions to avoid issues reading
RUN touch .secret
RUN chmod 600 .secret

# Copy the project files
COPY ./src/pyproject.toml ./
COPY ./src/poetry.lock ./

# Install dependecies trough poetry
RUN poetry install $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
    --no-interaction --no-ansi --sync

# Copy the source code
COPY ./src/ ./

USER root
RUN chown -R celery:pymap /home/celery/app/
USER celery

# celery -A pymap.celery worker -E --pool=gevent --statedb=celery/working.state"
CMD ["sh", "-c", "sleep 5 && $(poetry env info --path)/bin/celery -A pymap.celery worker -l INFO --concurrency=500 --pool=gevent"]
# For debbuging
#CMD ["tail", "-f", "/dev/null"]