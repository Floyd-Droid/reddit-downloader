from django.urls import path

from .tasks import(
    begin_auth,
    authorize,
)

from .views import (
    LoginView,
    SearchView,
    SearchResultsView,
    SearchHistoryView,
    PreviousSearchView,
    RemoveQueriesView,
    GenerateFilesView,
    DownloadView,
    LogoutView
)

app_name = 'downloader'

urlpatterns = [
    path('begin-authorization/', begin_auth, name='begin-authorization'),
    path('authorize/', authorize, name='authorize'),
    path('', LoginView.as_view(), name='login'),

    path('search/', SearchView.as_view(), name='search-main'),
    path('search/results/<int:pk>/', SearchResultsView.as_view(), name='search-results'),
    path('search/<str:type>/', SearchHistoryView.as_view(), name='search-history-or-favorites'),
    path('search/history/<int:pk>/', PreviousSearchView.as_view(), name='previous-search-main'),
    path('search/history/remove/', RemoveQueriesView.as_view(), name='remove-queries'),

    path('generate/<int:pk>', GenerateFilesView.as_view(), name='generate-files'),
    path('download/<int:pk>/<str:tmp>', DownloadView.as_view(), name='download'),
    path('logout/', LogoutView.as_view(), name='logout')
]