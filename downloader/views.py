from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic.base import View 
from django.views.generic import ( 
    FormView,
    DetailView
)
from reddit_downloader.settings import production as settings
from .export import (
    download_results
)
from .forms import (
    SearchForm,
    DownloadForm
)
from .models import (
    User,
    SearchQuery,
)
from .tasks import (
    get_results,
    get_submission_data_by_url,
)
import json
import os
import shutil
import zipfile


class LoginView(View):
    template_name = 'authorization/login.html'

    def get(self, request, *args, **kwargs):
        if request.session.get('authenticated', False):
            return redirect(reverse('downloader:search-main'))
        else:
            return render(request, self.template_name, {})


class SearchView(View):
    template_name = 'downloader/search_view.html'
    model = SearchQuery
    form_class = SearchForm

    def get(self, request, *args, **kwargs):
        auth = request.session.get('authenticated', False)
        context = {
            'form': self.form_class,
            'authenticated': auth
            }
        return render(request, self.template_name, context)
    
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
                if request.session.get('authenticated', False) is True:
                    # Add user to search query object
                    username = self.request.session["current_user"]
                    query.user = User.objects.get(username=username)
                query.save()
            else:
                auth = request.session.get('authenticated', False)
                context = {
                    'form': form,
                    'authenticated': auth}
                return render(self.request, self.template_name, context)

        return redirect(reverse('downloader:search-results', kwargs={'pk': query.pk}))


class SearchResultsView(View):
    """Display the results of a Search Query."""
    template_name = 'downloader/search_results.html'
    download_form = DownloadForm

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        query = self.get_object()
        if query.url:
            results = get_submission_data_by_url(query.url)
        else:
            results, non_existent_subreddits, forbidden_subreddits = get_results(query)

            # If any subreddits do not exist or are forbidden, inform the user that they were ignored.
            if non_existent_subreddits:
                subs_str = ', '.join(non_existent_subreddits)
                messages.info(request, f"The following subreddits do not exist: {subs_str}.")
            
            if forbidden_subreddits:
                subs_str = ', '.join(forbidden_subreddits)
                messages.info(request, f"The following subreddits are forbidden: {subs_str}.")

        auth = request.session.get('authenticated', False)
        context = {
            'query': query,
            'results': results,
            'form': self.download_form,
            'authenticated': auth
        }
        return render(request, self.template_name, context)


class PreviousSearchView(FormView):
    template_name = 'downloader/search_view.html'
    model = SearchQuery

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        q = self.get_object()
        form = SearchForm(instance=q, edit=True)
        auth = request.session.get('authenticated', False)
        context = {
            'form': form,
            'authenticated': auth
        }
        return render(request, self.template_name, context)


class SearchHistoryView(UserPassesTestMixin, DetailView):
    template_name = 'downloader/search_history_or_faves.html'

    def test_func(self):
        return self.request.session.get('authenticated', False)

    def get(self, request, *args, **kwargs):
        username = request.session["current_user"]
        last_clear = User.objects.get(username=username).last_clear_datetime
        type_ = self.kwargs.get('type')
        if type_ == 'history':
            queries = SearchQuery.objects.filter(user=username, date_created__gt=last_clear).order_by('-date_created')
        else:
            queries = SearchQuery.objects.filter(user=username, favorite=True).order_by('-date_created')

        auth = request.session.get('authenticated', False)
        context = {
            'queries': queries,
            'type': type_,
            'authenticated': auth
        }
        return render(request, self.template_name, context)


class RemoveQueriesView(UserPassesTestMixin, View):

    def test_func(self):
        return self.request.session.get('authenticated', False)

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
                return JsonResponse({'error': 'Something went wrong'}, status=400)
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({'error': 'Request is not ajax.'}, status=400)    


class GenerateFilesView(FormView):
    form_class = DownloadForm

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def post(self, request, *args, **kwargs):
        query = self.get_object()
        if request.is_ajax:
            form = DownloadForm(data=request.POST)
            if form.is_valid():
                sub_str = request.POST.get('sub_ids')
                sub_ids = json.loads(sub_str)
                tmp_dirname = download_results(query, form.cleaned_data, sub_ids)

                # Return the url that generates/downloads the files in the response
                url = reverse('downloader:download', kwargs={'pk': query.pk, 'tmp':tmp_dirname})
                return JsonResponse({'url': url}, status=200)
            else:
                return JsonResponse({'error': form.errors.as_json()}, status=400)
        else:
            return JsonResponse({'error': 'Request is not ajax.'}, status=400)


class DownloadView(View):

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(SearchQuery, pk=id_)

    def get(self, request, *args, **kwargs):
        dirname = self.kwargs.get('tmp')
        tmp_path = os.path.join(settings.MEDIA_ROOT, dirname)
        zname = 'results.zip'

        response = HttpResponse(content_type='application/zip')
        with zipfile.ZipFile(response, 'w') as f:
            # Place each generated file into the zip file
            for folder_name, sub_folders, filenames in os.walk(tmp_path):
                for filename in filenames:
                    filepath = os.path.join(folder_name, filename)
                    zip_path = os.path.join(folder_name.split('/')[-1], os.path.basename(filepath))
                    f.write(filepath, zip_path)

        response['Content-Disposition'] = 'attachment; filename={}'.format(zname)
        # Delete the generated files
        shutil.rmtree(tmp_path)

        return response


class LogoutView(View):

    def get(self, request, *args, **kwargs):
        request.session.clear()
        return redirect(reverse('downloader:login'))
