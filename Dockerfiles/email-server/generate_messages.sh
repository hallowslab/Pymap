#!/bin/bash

# Configuration
sender="pymap@mail.pymap.lan"
recipients=("pymap@mail.pymap.lan" "test@mail.pymap.lan")
dataset_path="/var/lib/spamassassin-dataset"  # Path to your email files

for recipient in "${recipients[@]}"; do
  # Loop through email files in dataset directory
  for email_file in "$dataset_path"/*; do
    # Ensure we only process regular files
    if [[ -f "$email_file" ]]; then
      # Inject the email to the specified recipient using Postfix's sendmail
      sendmail -f "$sender" "$recipient" < "$email_file"
      echo "Injected $(basename "$email_file") to $recipient"
    fi
  done
done