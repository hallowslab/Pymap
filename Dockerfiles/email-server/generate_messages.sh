#!/bin/bash

# Configuration
sender="pymap@mail.pymap.lan"
recipients=("pymap@mail.pymap.lan" "test@mail.pymap.lan")
num_messages=5000
subjects_file="subjects.txt"
bodies_file="bodies.txt"

# Load random subjects and bodies from external files
generate_random_subject() {
  shuf -n 1 "$subjects_file"
}

generate_random_body() {
  shuf -n 1 "$bodies_file"
}

# Loop through recipients and send multiple emails
for recipient in "${recipients[@]}"; do
  for ((i = 1; i <= num_messages; i++)); do
    subject=$(generate_random_subject)
    body=$(generate_random_body)

    # Send the email
    echo "Generating message from $sender to $recipient" >> generate.txt
    echo "$body" | mail -s "$subject" -r "$sender" "$recipient"
    
    echo "Sent email #$i to $recipient with subject '$subject'"
  done
done
