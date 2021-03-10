from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic.base import View 
from django.views.generic import ( 
    FormView,
    DetailView
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
import json


class LoginView(View):
    template_name = 'authorization/login.html'

    def get(self, request, *args, **kwargs):
        context = {
            "auth_url": AUTH_URL
        }
        return render(request, self.template_name, context)


class SearchView(View):
    template_name = 'downloader/search_view.html'
    model = SearchQuery
    form_class = SearchForm
    context = {
        'form': form_class
    }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
    
    def post(self, request, *args, **kwargs):
        # If re-doing a search, create a new query from the existing one.
        id_ = request.POST.get('redo', None)
        if id_ is not None:
            old_query = SearchQuery.objects.get(pk=id_)
            new_query = old_query
            new_query.pk = None
            new_query.save()
        else:
            form = self.form_class(data=request.POST)
            if form.is_valid():
                query = form.save(commit=False)
                # Add user to search query object
                username = self.request.session["current_user"]
                query.user = User.objects.get(username=username)
                query.save()
            else:
                self.context['form'] = form
                return render(self.request, self.template_name, self.context)

        return redirect(reverse('downloader:search-results', kwargs={'pk': query.pk}))
        

class SearchResultsView(View):
    """Display the results of a Search Query."""
    template_name = 'downloader/search_results.html'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        query = self.get_object()
        results = get_results(query)
        context = {
            'results': results,
        }
        return render(self.request, self.template_name, context)


class PreviousSearchView(FormView):
    template_name = 'downloader/search_view.html'
    model = SearchQuery

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        q = self.get_object()
        form = SearchForm(instance=q)
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


class SearchHistoryView(DetailView):
    template_name = 'downloader/search_history_or_faves.html'

    def get(self, request, *args, **kwargs):
        username = request.session["current_user"]
        last_clear = User.objects.get(username=username).last_clear_datetime
        type_ = self.kwargs.get('type')
        if type_ == 'history':
            queries = SearchQuery.objects.filter(user=username, date_created__gt=last_clear).order_by('-date_created')
        else:
            queries = SearchQuery.objects.filter(user=username, favorite=True).order_by('-date_created')

        context = {
            'queries': queries,
            'type': type_
        }
        return render(request, self.template_name, context)


class RemoveQueriesView(View):

    def post(self, request, *args, **kwargs):
        if request.is_ajax:
            id_str = request.POST.get('query_ids')
            ids = json.loads(id_str)
            objs = SearchQuery.objects.filter(pk__in=ids)

            username = request.session.get('current_user')
            user = User.objects.get(username=username)

            if 'remove-queries' in request.POST:
                # Delete all queries except those marked as favorites.
                objs.filter(favorite=False).delete()
                # Update the user's last_clear_datetime
                user.last_clear_datetime = timezone.now()
                user.save()
            elif 'remove-faves' in request.POST:
                objs.filter(date_created__lt=user.last_clear_datetime).delete()
                objs.filter(date_created__gt=user.last_clear_datetime).update(favorite=False)
            elif 'add-faves' in request.POST:
                objs.update(favorite=True)
            else:
                print("Something went wrong")
                return JsonResponse({'error': '???'}, status=400)
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({'error': 'Request is not ajax.'}, status=400)    
