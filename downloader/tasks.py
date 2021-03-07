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
        permalink = 'https://www.reddit.com' + sub.permalink
        sub_data.append({'title': sub.title, 'id': sub.id, 'score': sub.score, 'permalink': permalink, \
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
    exclude = [sub.replace('!', '') for sub in sub_list if sub.startswith('!')]

    lim = query.limit
    submissions_to_keep = []
    last = None
    count = 0

    # Retrieve valid results until the limit is reached.
    while len(submissions_to_keep) < query.limit:
        if query.terms:
            subreddit = reddit.subreddit('+'.join(include))
            submissions = subreddit.search(
                query=query.terms,
                syntax=query.syntax, 
                sort=query.praw_sort, 
                time_filter=query.time_filter, 
                limit=lim,
                params={'after':last}
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
                # Exclusions are accounted for in the sub_str here.
                exclude = []

            if query.praw_sort == 'hot':
                submissions = subreddit.hot(limit=lim, params={'after':last}) 
            elif query.praw_sort == 'top':
                submissions = subreddit.top(time_filter=query.time_filter, params={'after':last}) 
            elif query.praw_sort == 'new':
                submissions = subreddit.new(limit=lim, params={'after':last}) 
            elif query.praw_sort == 'controversial':
                submissions = subreddit.controversial(time_filter=query.time_filter, limit=lim, params={'after':last}) 
            elif query.praw_sort == 'rising':
                submissions = subreddit.rising(limit=lim, params={'after':last}) 
            elif query.praw_sort == 'random rising':
                submissions = subreddit.random_rising(limit=lim, params={'after':last}) 
        
        # If the length of the list remains the same over multiple iterations, we have
        # likely retrieved all possible results for this search.
        len1 = len(submissions_to_keep)

        # Find submissions to keep: ignore stickied, removed, or deleted posts, as well as excluded subreddits.
        submissions_to_keep += [sub for sub in submissions if sub.subreddit not in exclude and \
            sub.stickied is False and sub.selftext not in ['[removed]', '[deleted]']]
        len2 = len(submissions_to_keep)
        # Break if the length of submissions does not change for 5 iterations
        if len1 == len2:
            if count == 5:
                break
            else:
                count += 1

        lim = query.limit - len(submissions_to_keep)
        # Use the fullname of the last submission as a starting point for the next search.
        last = submissions_to_keep[-1].fullname
 
    results = get_submission_data(submissions_to_keep)
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
    sub_str = ','.join(sub_list)

    lim = query.limit
    submissions_to_keep = []
    last = None
    count = 0

    while len(submissions_to_keep) < query.limit:

        submissions = list(api.search_submissions(
            q=query.terms, 
            subreddit=sub_str, 
            limit=lim, 
            after=start_date,
            before=end_date, 
            sort_type=query.psaw_sort, 
            params={'after':last}
        ))

        len1 = len(submissions_to_keep)
        # Find submissions to keep: ignore stickied, removed, or deleted posts.
        submissions_to_keep += [sub for sub in submissions if sub.stickied is False and \
            sub.selftext not in ['[removed]', '[deleted]']]
        len2 = len(submissions_to_keep)

        if len1 == len2:
            if count == 5:
                break
            else:
                count += 1
        lim = query.limit - len(submissions_to_keep)

    results = get_submission_data(submissions_to_keep)
    return results
