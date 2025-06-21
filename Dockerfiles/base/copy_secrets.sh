#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Running copy_secrets.sh"

# Determine the home dir of the current user
USER_HOME=$(eval echo ~"$(whoami)")
SECRETS_DIR="/run/secrets"
APP_DIR="$USER_HOME/app"

declare -A FILE_MAP=(
  [".pg_service.conf"]="$USER_HOME/.pg_service.conf"
  [".pgpass"]="$APP_DIR/.pgpass"
  [".secret"]="$APP_DIR/.secret"
)

# Copy secrets if they exist
for src_file in "${!FILE_MAP[@]}"; do
    src_path="$SECRETS_DIR/$src_file"
    dest_path="${FILE_MAP[$src_file]}"

    if [ -f "$src_path" ]; then
        cp "$src_path" "$dest_path"
        echo "[INFO] Copied $src_file to $dest_path"

        # Secure permissions
        chmod 600 "$dest_path"
        chown "$(whoami):pymap" "$dest_path"
        echo "[INFO] Set ownership and permissions for $dest_path"
    else
        echo "[WARN] Secret file $src_path not found; skipping"
    fi
done
