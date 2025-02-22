# filter/urls.py

from django.urls import path

from .views import upload_image_api, check_status_api
from . import views

urlpatterns = [
    path('', views.index),
    path('upload/', upload_image_api, name='upload_image_api'),
    path('status/<int:image_id>/', check_status_api, name='check_status_api'),
]


