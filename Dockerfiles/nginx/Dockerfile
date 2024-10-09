# Use an official Nginx image
FROM nginx:latest

ARG STATIC_ROOT \
    GROUPNAME \
    GID \
    PYMAP_HOSTNAME

# nginx parses variables as lower case??
# https://stackoverflow.com/questions/57676371/nginx-variables-ignore-case
ENV static_root=${STATIC_ROOT} \
    STATIC_ROOT=${STATIC_ROOT}

# Install envsubst
RUN apt-get update && \
    apt-get install -y gettext-base openssl && \
    rm -rf /var/lib/apt/lists/*

# Create SSL directory
RUN mkdir -p /etc/ssl/private /etc/ssl/certs

# Generate self-signed SSL certificate and private key
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=PT/ST=Lisbon/L=Lisbon/O=Pymap/OU=Tech/CN=$PYMAP_HOSTNAME"

RUN addgroup --gid $GID $GROUPNAME

# Create $STATIC_ROOT
RUN mkdir -p $STATIC_ROOT
# Add permissions for group keep user on root for nginx container
RUN chown -R root:$GROUPNAME $STATIC_ROOT && chmod -R g+rw $STATIC_ROOT

# Copy Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/nginx.template

RUN envsubst '$STATIC_ROOT' < /etc/nginx/conf.d/nginx.template > /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]

#CMD ["tail", "-f", "/dev/null"]
