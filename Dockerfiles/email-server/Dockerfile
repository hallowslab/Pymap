FROM ubuntu:22.04

ARG HOSTNAME \
	SMTP_PORT \
	SMTP_SUBMISSION \
	IMAP_PORT

ENV GENERATE_MESSAGES=${GENERATE_MESSAGES}

# Install Postfix and Dovecot
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y postfix dovecot-core dovecot-imapd dovecot-pop3d net-tools telnet mailutils rsyslog

# Modify Postfix Configuration
RUN sed -i "s/^myhostname.*/myhostname = ${HOSTNAME}/" /etc/postfix/main.cf && \
	sed -i 's/^#myorigin.*/myorigin = $mydomain/' /etc/postfix/main.cf && \
	sed -i 's/^mydestination.*/mydestination = $myhostname, $mydomain, localhost.$mydomain, localhost/' /etc/postfix/main.cf && \
	sed -i 's/^inet_interfaces.*/inet_interfaces = all/' /etc/postfix/main.cf

RUN echo "mydomain = ${HOSTNAME}" >> /etc/postfix/main.cf && \
	echo "home_mailbox = Maildir/" >> /etc/postfix/main.cf

# Modify Dovecot Configuration
RUN sed -i 's/^mail_location.*/mail_location = maildir:~\/Maildir/' /etc/dovecot/conf.d/10-mail.conf && \
    sed -i 's/^#disable_plaintext_auth.*/disable_plaintext_auth = no/' /etc/dovecot/conf.d/10-auth.conf && \
	sed -i 's/^#auth_username_format =.*/auth_username_format = %n/' /etc/dovecot/conf.d/10-auth.conf && \
    sed -i "s/#port = 143/port = ${IMAP_PORT}/" /etc/dovecot/conf.d/10-master.conf && \
    sed -i "s/#port = 587/port = ${SMTP_SUBMISSION}/" /etc/dovecot/conf.d/10-master.conf && \
	sed -i 's/^#log_path.*/log_path = \/var\/log\/dovecot.log/' /etc/dovecot/conf.d/10-logging.conf

RUN useradd -m pymap -p pymap -s /bin/false && \
	echo "pymap:Password123"|chpasswd && \
	mkdir /home/pymap/Maildir && \
	chown pymap:pymap /home/pymap/Maildir/

RUN useradd -m test -p test -s /bin/false && \
	echo "test:Password123"|chpasswd && \
	mkdir /home/test/Maildir && \
	chown test:test /home/test/Maildir/

RUN touch /var/log/postfix.log
RUN chmod 640 /var/log/postfix.log
RUN chown postfix:postfix /var/log/postfix.log

RUN touch /var/log/dovecot.log
RUN chmod 640 /var/log/dovecot.log
RUN chown dovecot:dovecot /var/log/dovecot.log

COPY init.sh init.sh
COPY bodies.list bodies.txt
COPY subjects.list subjects.txt
COPY generate_messages.sh generate_messages.sh

CMD ["sh", "-c", "./init.sh"]
