service dovecot start
service postfix start

start_dir=$PWD

# Check if GENERATE_MESSAGES environment variable is set to 'true'
if [ "$GENERATE_MESSAGES" = "true" ]; then
    # Get the apache spamassassin ham dataset from https://spamassassin.apache.org/old/publiccorpus/
    echo "Fetching samples from spamassassin dataset";
    mkdir -p /var/lib/spamassassin-dataset;
    cd /var/lib/spamassassin-dataset;
    sleep 2;
    curl -o easy_ham.tar.bz2 https://spamassassin.apache.org/old/publiccorpus/20021010_easy_ham.tar.bz2;
    curl -o easy_ham2.tar.bz2 https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham.tar.bz2;
    curl -o hard_ham.tar.bz2 https://spamassassin.apache.org/old/publiccorpus/20021010_hard_ham.tar.bz2;
    curl -o hard_ham2.tar.bz2 https://spamassassin.apache.org/old/publiccorpus/20030228_hard_ham.tar.bz2;
    tar -xvjf easy_ham.tar.bz2 --strip-components=1;
    tar -xvjf easy_ham2.tar.bz2 --strip-components=1;
    tar -xvjf hard_ham.tar.bz2 --strip-components=1;
    tar -xvjf hard_ham2.tar.bz2 --strip-components=1;
    rm -f easy_ham.tar.bz2 easy_ham2.tar.bz2 hard_ham.tar.bz2 hard_ham2.tar.bz2;
    cd $start_dir;
    # Call the script to generate and send messages
    echo "Generating Messages";
    ./generate_messages.sh
fi

tail -f /var/log/dovecot.log /var/log/postfix.log /var/log/mail.log