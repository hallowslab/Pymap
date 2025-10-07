from celery import shared_task
import time

@shared_task
def ping():
    time.sleep(2)  # simulate a small delay
    return "pong!"
