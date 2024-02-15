FROM alpine:3.15

RUN set -xe

# Install postfix, dovecot, and other required tools
RUN apk update && apk upgrade && apk add --no-cache postfix dovecot supervisor mailx
# Add user for nginx
#RUN adduser -D -g 'www' www

# supervisor log directories
RUN mkdir -p /var/log/supervisor

# Enable edge repos
#RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories
#RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
#RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
#RUN cat /etc/apk/repositories

# Postfix directories and permissions
RUN mkdir -p /var/spool/postfix /var/spool/postfix/public /var/spool/postfix/pickup
RUN chown root:postfix /var/spool/postfix
RUN chown -R postfix:postdrop /var/spool/postfix/public
RUN chown -R postfix:postdrop /var/spool/postfix/pickup
RUN touch /var/log/postfix.log && chown postfix:postfix /var/log/postfix.log

#RUN ["sh", "-c", "/usr/sbin/postfix set-permissions --help"]

# Copy configuration files
COPY postfix/main.cf /etc/postfix/main.cf
COPY dovecot/dovecot.conf /etc/dovecot/dovecot.conf
COPY supervisord.conf /etc/supervisord.conf

# Enable port 4600 on postfix
RUN echo "4600      inet  n       -       n       -       -       smtpd" >> /etc/postfix/master.cf

# Add script to create accounts and messages
COPY setup.sh /usr/local/bin/setup.sh

# Expose required ports
EXPOSE 2500 1430 4650 9930

#RUN which mail
RUN ["sh", "-c", "/usr/local/bin/setup.sh"]

# For interactive prompt
#CMD ["sh", "-c", "tail -f /dev/null"]

# Start services using supervisord
CMD ["supervisord", "-c", "/etc/supervisord.conf"]