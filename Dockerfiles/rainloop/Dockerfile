FROM alpine:3.15

RUN set -xe

RUN apk update && apk upgrade && apk add --no-cache nginx supervisor busybox-extras

# supervisor log directories
RUN mkdir -p /var/log/supervisor

# Install PHP-FPM
RUN apk --update add php7-fpm php7-json php7-session php7-openssl php7-curl php7-zip php7-xml php7-gettext php7-mbstring php7-iconv php7-fileinfo php7-dom

# Install Rainloop
RUN mkdir -p /var/www/rainloop \
   && wget -qO- https://www.rainloop.net/repository/webmail/rainloop-latest.zip | unzip -d /var/www/rainloop -

# Copy rainloop config
COPY rainloop/config.ini /var/www/rainloop/data/_data_/_default_/configs/config.ini
COPY rainloop/config.ini /var/www/rainloop/data/_data_/localhost/configs/config.ini

# Fix permissions according to docs
RUN find /var/www/rainloop -type d -exec chmod 755 {} \;
RUN find /var/www/rainloop -type f -exec chmod 644 {} \;
# Update ownership
RUN chown -R nginx:nginx /var/www/rainloop
# Update data permissions
RUN chmod -R 755 /var/www/rainloop/data

# Copy configuration files
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY php-fpm/www.conf /etc/php7/php-fpm.d/www.conf
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 8080

# Start services using supervisord
CMD ["supervisord", "-c", "/etc/supervisord.conf"]