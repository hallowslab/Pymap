#!/usr/bin/env bash
set -e

# Determine the home dir of the current user
USER_HOME=$(eval echo ~$(whoami))

# Copy secrets if they exist
[ -f /run/secrets/.pg_service.conf ] && cp /run/secrets/.pg_service.conf "$USER_HOME/.pg_service.conf"
[ -f /run/secrets/.pgpass ] && cp /run/secrets/.pgpass "$USER_HOME/app/.pgpass"
[ -f /run/secrets/.secret ] && cp /run/secrets/.secret "$USER_HOME/app/.secret"

# Secure permissions
chmod 600 "$USER_HOME/.pg_service.conf" "$USER_HOME/app/.pgpass" "$USER_HOME/app/.secret"
chown "$(whoami)":pymap "$USER_HOME/.pg_service.conf" "$USER_HOME/app/.pgpass" "$USER_HOME/app/.secret"
