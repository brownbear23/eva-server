## filter/celery.py
# Sets up Celery, a distributed task queue
# Configures Celery to load settings from Django and discover tasks.


from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('eva-server')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
