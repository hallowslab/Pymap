service dovecot start
service postfix start

# Check if GENERATE_MESSAGES environment variable is set to 'true'
if [ "$GENERATE_MESSAGES" = "true" ]; then
    # Call the script to generate and send messages
    ./generate_messages.sh
fi

tail -f /var/log/dovecot.log /var/log/postfix.log /var/log/mail.log