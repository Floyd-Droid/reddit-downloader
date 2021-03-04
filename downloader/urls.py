from django.urls import path

from .views import (
    SearchView,
    SearchResultsView,
)

app_name = 'downloader'

urlpatterns = [
    path('search/', SearchView.as_view(), name='search-home'),
    path('search/results/<int:pk>', SearchResultsView.as_view(), name='search-results'),
]