from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingSystem.settings')

app = Celery('ParkingSystem')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Settings
app.conf.beat_schedule = {
    'schedule-booking-reminders': {
        'task': 'parking_app.tasks.schedule_booking_reminders',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'check-over-parking': {
        'task': 'parking_app.tasks.check_over_parking',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
