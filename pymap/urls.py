from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="pymap_home"),
    path('test-celery/', views.test_celery, name='pymap_test-celery'),
]
