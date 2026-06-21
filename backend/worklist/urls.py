from django.urls import path

from .views import WorklistView

urlpatterns = [
    path('worklist/', WorklistView.as_view(), name='worklist'),
]
