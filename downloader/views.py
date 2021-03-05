from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import View 
from django.views.generic import ( 
    FormView,
)
from .forms import (
    SearchForm,
)
from .models import (
    SearchQuery,
)

import praw
import uuid
import datetime
import environ

env = environ.Env()
environ.Env.read_env()

reddit = praw.Reddit(
    client_id=env.str('CLIENT_ID'),
    client_secret=env.str('CLIENT_SECRET'),
    user_agent='jf_downloader',
    redirect_uri = 'http://localhost:8000/authorize'
)

scopes = ['*']
state = str(uuid.uuid4())
auth_url = reddit.auth.url(scopes, state)

def authorize(request):
    """
    User is redirected here after successful login with Reddit.
    Set the access token to the reddit instance and redirect to search page.
    """
    returned_state = request.GET.get('state', None)
    auth_code = request.GET.get('code', None)
    error = request.GET.get('error', None)

    #TODO - handle these cases
    if returned_state != state:
        print("UNAUTHORIZED")
        return 'Unauthorized'  

    if error:
        print(error)
        return

    if auth_code is None:
        print("MISSING CODE")
        return 'Missing access token'

    # Use the code to authorize our reddit instance
    reddit.auth.authorize(auth_code)  

    return redirect(reverse('downloader:search-home'))

def get_results(query):
    pass


class LoginView(View):
    template_name = 'authorization/login.html'
    context = {
        "auth_url": auth_url
    }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)


class SearchView(FormView):
    template_name = 'downloader/search_view.html'
    model = SearchQuery
    form_class = SearchForm
    context = {
        'form': form_class
    }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
    
    def form_valid(self, form):
        query = form.save()
        return redirect(reverse('downloader:search-results', kwargs={'pk': query.pk}))
    
    def form_invalid(self, form):
        self.context['form'] = form
        return render(self.request, self.template_name, self.context)


class SearchResultsView(View):
    """Display the results of a Search Query."""
    template_name = 'downloader/search_results.html'
    model = SearchQuery
    form_class = SearchForm

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        query = self.get_object()
        results = get_results(query)
        context = {
            'results': results
        }
        return render(self.request, self.template_name, context)
