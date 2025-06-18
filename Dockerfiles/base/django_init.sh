#!/usr/bin/env bash

# Wait for all systems to start
#sleep 5
echo "Running init.sh..." > django_init.txt

# --- Copy secrets ---
/home/pymap/copy_secrets.sh

# Check for migrations
echo "Running DB migration check..."
if ! /home/pymap/app/.venv/bin/python manage.py migrate --no-input --check >> django_init.txt; then
    echo "Running migrations" >> django_init.txt
    /home/pymap/app/.venv/bin/python manage.py migrate --no-input >> django_init.txt
else
    echo "No migrations needed" >> django_init.txt
fi

# Run the initadmin command
echo "Running initadmin command" >> django_init.txt
/home/pymap/app/.venv/bin/python manage.py initadmin >> django_init.txt

# Run the create_management_group command
echo "Running create_management_groups command" >> django_init.txt
/home/pymap/app/.venv/bin/python manage.py create_management_groups >> django_init.txt

# Import fixtures, and other data
echo "Importing fixtures...." >> django_init.txt
/home/pymap/app/.venv/bin/python manage.py loaddata periodic.json
/home/pymap/app/.venv/bin/python manage.py loaddata purge_results.json
/home/pymap/app/.venv/bin/python manage.py loaddata delete_mothly.json

# Collect static assets 
/home/pymap/app/.venv/bin/python manage.py collectstatic --no-input

# Start the application
echo "Starting app..." >> django_init.txt
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production server" >> django_init.txt
    /home/pymap/app/.venv/bin/python -m gunicorn pymap.asgi:application -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
else
    echo "Starting development server" >> django_init.txt
    /home/pymap/app/.venv/bin/python manage.py runserver 0.0.0.0:8000
fi
