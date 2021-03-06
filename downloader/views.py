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
    User,
    SearchQuery,
)
from .tasks import (
    AUTH_URL,
    get_results,
    get_submission_data,
    get_praw_submissions,
    get_psaw_submissions,
)


class LoginView(View):
    template_name = 'authorization/login.html'

    def get(self, request, *args, **kwargs):
        context = {
            "auth_url": AUTH_URL
        }
        return render(request, self.template_name, context)


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
        query = form.save(commit=False)
        # Add user to search query object
        username = self.request.session["current_user"]
        query.user = User.objects.get(username=username)
        query.save()
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
