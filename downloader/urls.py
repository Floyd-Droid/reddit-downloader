from django.urls import path

from .tasks import(
    authorize
)

from .views import (
    LoginView,
    SearchView,
    SearchResultsView,
)

app_name = 'downloader'

urlpatterns = [
    path('authorize/', authorize, name='authorize'),
    path('', LoginView.as_view(), name='login-page'),

    path('search/', SearchView.as_view(), name='search-main'),
    path('search/results/<int:pk>/', SearchResultsView.as_view(), name='search-results'),
]