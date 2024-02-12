FROM python:3.11

WORKDIR /app

RUN set -xe

# Install imapsync dependencies
RUN apt-get update && \
    apt-get install -y apt-file make gcc cpanminus libtest-mock-guard-perl \
    libjson-webtoken-perl libjson-perl libpar-packer-perl libwww-perl

# Required for imapsync dependecy check
RUN apt-file update

# Perl modules for imapsync
RUN cpanm Mail::IMAPClient Authen::NTLM CGI Crypt::OpenSSL::RSA Data::Uniqid \
    Digest::HMAC Digest::HMAC_MD5 Dist::CheckConflicts Encode::IMAPUTF7 File::Copy::Recursive \
    File::Tail IO::Socket::INET6 IO::Socket::SSL IO::Tee JSON JSON::WebToken::Crypt::RSA \
    LWP::UserAgent Module::ScanDeps Net::SSLeay Proc::ProcessTable Regexp::Common \
    Sys::MemInfo Term::ReadKey Test::Fatal Test::MockObject Test::Pod \
    Test::Requires Test::Deep Unicode::String


# Clone and install imapsync
RUN git clone https://github.com/imapsync/imapsync.git

RUN cd imapsync && make install

# Poetry install
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry --version

# copy the app
COPY ./src /app/

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "poetry shell && python manage.py runserver 0.0.0.0:8000"]