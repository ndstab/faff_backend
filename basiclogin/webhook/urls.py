from django.urls import path
from . import views

urlpatterns = [
    path('', views.whatsapp_webhook, name='whatsapp_webhook'),
]
