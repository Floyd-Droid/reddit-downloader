from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from .models import (
    SearchQuery,
    User
)

import datetime
import praw
from psaw import PushshiftAPI
import environ
import uuid

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
AUTH_URL = reddit.auth.url(scopes, state)

api = PushshiftAPI(reddit)

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

    # Use the code to authorize our reddit instance, and save the user's name to session.
    reddit.auth.authorize(auth_code)  
    request.session["authenticated"] = True
    request.session["current_user"] = str(reddit.user.me())

    # Add user to database if not present.
    username = request.session["current_user"]
    if not User.objects.filter(username=username).exists():
        new_user = User.objects.create(username=username)
        new_user.save()

    return redirect(reverse('downloader:search-home'))


def get_submission_data(submissions):
    """From the passed generator, get submission data as a list of dictionaries."""
    sub_data = []
    for sub in submissions:
        date_created = datetime.datetime.fromtimestamp(sub.created)
        sub_data.append({'title': sub.title, 'id': sub.id, 'score': sub.score, 'permalink': sub.permalink, \
            'url': sub.url, 'num_comments': sub.num_comments, 'date': date_created, 'selftext': sub.selftext})

    return sub_data

def get_results(query: SearchQuery):
    """Determine which function is used to grab search results."""
    if query.praw_sort is not None:              
        results = get_praw_submissions(query)
    elif query.psaw_sort is not None:
        results = get_psaw_submissions(query)
    else:
        pass

    return results

def get_praw_submissions(query: SearchQuery):
    """Grab submissions using PRAW based on the SearchQuery object."""
    sub_list = query.subreddit.split(',')

    # Get a list of subreddits to be included and excluded from the search.
    include = [sub for sub in sub_list if not sub.startswith('!')]

    if query.terms:
        subreddit = reddit.subreddit('+'.join(include))
        submissions = subreddit.search(
            query=query.terms,
            syntax=query.syntax, 
            sort=query.praw_sort, 
            time_filter=query.time_filter, 
            limit=query.limit,
        )
    else: 
        # Set up all possible reddit sorts without search terms
        if 'front' in sub_list:
            subreddit = reddit.front
        else:
            # PRAW uses + and - to chain subreddits
            sub_str = query.subreddit.replace(',!', '-')
            sub_str = sub_str.replace(',', '+')
            subreddit = reddit.subreddit(sub_str)

        if query.praw_sort == 'hot':
            submissions = subreddit.hot(limit=query.limit) 
        elif query.praw_sort == 'top':
            submissions = subreddit.top(time_filter=query.time_filter) 
        elif query.praw_sort == 'new':
            submissions = subreddit.new(limit=query.limit) 
        elif query.praw_sort == 'controversial':
            submissions = subreddit.controversial(time_filter=query.time_filter, limit=query.limit) 
        elif query.praw_sort == 'rising':
            submissions = subreddit.rising(limit=query.limit) 
        elif query.praw_sort == 'random rising':
            submissions = subreddit.random_rising(limit=query.limit) 
 
    results = get_submission_data(submissions)
    return results


def get_psaw_submissions(query: SearchQuery):
    """Grab submissions using PSAW based on the SearchQuery object."""

    # Convert user input date to utc
    start_date = int(query.start_date.timestamp())
    end_date = int(query.end_date.timestamp())

    # Drop 'all' from subreddit list if it exists (invalid for psaw)
    sub_list = query.subreddit.split(',')
    if 'all' in sub_list:
        sub_list.remove('all')
    sub_str = ",".join(sub_list)

    submissions = list(api.search_submissions(q=query.terms, subreddit=sub_str, limit=query.limit, after=start_date, before=end_date, sort_type=query.psaw_sort))

    results = get_submission_data(submissions)
    return results
