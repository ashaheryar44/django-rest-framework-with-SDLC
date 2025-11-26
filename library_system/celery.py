import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')

app = Celery('library_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# Define your beat schedule here (optional, can be managed via Django admin)
app.conf.beat_schedule = {
    'run-daily-at-midnight': {
        'task': 'library.tasks.send_over_due_loan_notification',
        'schedule': crontab(minute=0, hour=0),
    },
}
