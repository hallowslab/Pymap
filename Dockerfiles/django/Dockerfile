FROM python:3.11

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

# Install imapsync dependencies
RUN apt-get update && \
    apt-get install -y apt-file make gcc cpanminus pipx libtest-mock-guard-perl libjson-webtoken-perl libjson-perl \
    libpar-packer-perl libwww-perl libpackage-stash-perl libpackage-stash-xs-perl libio-socket-inet6-perl

# Perl modules for imapsync
RUN cpanm Mail::IMAPClient Authen::NTLM CGI Crypt::OpenSSL::RSA Data::Uniqid \
    Digest::HMAC Digest::HMAC_MD5 Dist::CheckConflicts Encode::IMAPUTF7 File::Copy::Recursive \
    File::Tail IO::Socket::INET6 IO::Socket::SSL IO::Tee JSON JSON::WebToken::Crypt::RSA \
    LWP::UserAgent Module::ScanDeps Net::SSLeay Proc::ProcessTable Regexp::Common \
    Sys::MemInfo Term::ReadKey Test::Fatal Test::MockObject Test::Pod \
    Test::Requires Test::Deep Unicode::String

# Required for imapsync dependecy check
RUN apt-file update

# Clone and install imapsync
RUN git clone https://github.com/imapsync/imapsync.git
RUN cd imapsync && make install

# Poetry install
RUN pipx install poetry
# Add pipx executables to path
RUN pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/root/.local/bin:$PATH"

# copy the app
COPY ./src /app/

# Create the log directory
RUN mkdir -p /var/log/pymap

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "poetry shell && python manage.py runserver 0.0.0.0:8000"]