FROM debian:bookworm

# Needed for fixing permissions of files created by Docker:
ARG UID=1000 \
  GID=1000


ENV DJANGO_ENV=production \
  # python:
  PYTHONFAULTHANDLER=1 \
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
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

WORKDIR /app

# Install system and perl dependencies
RUN apt-get update && \
    apt-get install -y redis git curl tmux supervisor apt-file make time gcc lsb-release procps python3 pipx cpanminus \
    libauthen-ntlm-perl libcgi-pm-perl libcrypt-openssl-rsa-perl libdata-uniqid-perl libpar-packer-perl \
    libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl libio-socket-inet6-perl \
    libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl libtest-requires-perl \
    libparse-recdescent-perl libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libtest-mock-guard-perl \
    libsys-meminfo-perl libterm-readkey-perl libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl \
    libtest-nowarnings-perl libtest-deep-perl libtest-warn-perl libnet-server-perl libpackage-stash-perl libpackage-stash-xs-perl \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Perl modules for imapsync
# See https://imapsync.lamiral.info/FAQ.d/FAQ.SSL_errors.txt
RUN cpanm Dist::CheckConflicts Module::Implementation IO::Socket::SSL

# Required for imapsync dependecy check
RUN apt-file update

# Clone and install imapsync
RUN git clone https://github.com/imapsync/imapsync.git
RUN cd imapsync && make install

# Install poetry
RUN pipx install poetry
# Add pipx executables to path
RUN pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/root/.local/bin:$PATH"

# supervisor config
COPY Dockerfiles/aio/supervisord.conf /etc/supervisord.conf

# Copy lock and project file for caching purposes
COPY ./src/poetry.lock /app/poetry.lock
COPY ./src/pyproject.toml /app/pyproject.toml


# Project initialization:
# RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
#   echo "$DJANGO_ENV" \
#   && poetry install \
#     $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
#     --no-interaction --no-ansi --sync
RUN echo "$DJANGO_ENV" && poetry install

# copy the app
COPY ./src /app/

# Create the log directory
RUN mkdir -p /var/log/pymap

# makemigrations and migrate (required for aio in first time setup)
RUN poetry run task prepare && poetry run task migrate

# Handle tasks with supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
