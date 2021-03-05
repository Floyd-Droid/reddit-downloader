from django.urls import path

from .views import (
    authorize,
    LoginView,
    SearchView,
    SearchResultsView,
)

app_name = 'downloader'

urlpatterns = [
    path('authorize/', authorize, name='authorize'),
    path('', LoginView.as_view(), name='login-page'),

    path('search/', SearchView.as_view(), name='search-home'),
    path('search/results/<int:pk>', SearchResultsView.as_view(), name='search-results'),
]