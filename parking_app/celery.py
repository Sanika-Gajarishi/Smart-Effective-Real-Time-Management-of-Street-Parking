import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingSystem.settings')

app = Celery('ParkingSystem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-parking-10min-alerts': {
        'task': 'parking_app.tasks.send_parking_10min_alerts',
        'schedule': crontab(minute='*/1'),
    },
    'send-parking-expiry-reminders': {
        'task': 'parking_app.tasks.send_parking_expiry_reminders',
        'schedule': crontab(minute='*/5'),
    },
    'check-over-parking': {
        'task': 'parking_app.tasks.check_over_parking',
        'schedule': crontab(minute='*/1'),
    },
}
