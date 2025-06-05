# sentiment_analysis/urls.py
from django.urls import path
from .views import PredictSentimentView

urlpatterns = [
    path("analyze/", PredictSentimentView.as_view(), name="analyze"),
]
