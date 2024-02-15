#!/bin/sh

# VARS
user_list=""
hostname="example1.lan"
domain_list="$hostname example2.lan"
user_count=10
message_count=5

# Functions
# Function to generate a random text message
generate_random_message() {
    echo "Subject: Random Test Message\n\n$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 100)"
}

# Function to get a random item from a space separated list
get_random_item() {
    items="$@"
    # uses tr to convert the space-separated list to lines, then uses shuf and head to get a random line.
    random_item=$(echo "$items" | tr ' ' '\n' | shuf | head -n 1)
    echo "$random_item"
}

# Function to create a mail user to be used on loop
add_test_user() {
    user="user$1"
    address="$user@$2"
    echo "echo:Adding user $user"
    adduser -D -h "/home/$user" -s /sbin/nologin -g "Mail User" -G mail "$user"
    # Set passwords
    echo "$user:password$1" | chpasswd
    
    # Create mailbox directories
    echo "Creating directories under /var/mail/example*.lan for user $user"
    mkdir -p "/var/mail/$2/$user"
    user_list="$user_list $address"
}


# Add fake domains
echo "example1.lan" >> /etc/postfix/virtual_mailbox_domains
echo "example2.lan" >> /etc/postfix/virtual_mailbox_domains
postmap /etc/postfix/virtual_mailbox_domains

# Add user accounts
for i in $(seq 1 $user_count); do
    add_test_user $i $(get_random_item $domain_list)
done

# Loop to send random messages between random users
for i in $(seq 1 $message_count); do
    sender=$(get_random_item $user_list)
    recipient=$(get_random_item $user_list)
    
    message=$(generate_random_message)

    echo "Sending message $i from $sender to $recipient"
    #echo "$message" | mail -s "Test Message N$i" -r "$sender" $recipient
    echo "$message" | mail -s "Test Message N$i" $recipient
done