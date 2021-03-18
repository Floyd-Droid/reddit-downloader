from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from .models import (
    SearchQuery,
    User
)
from prawcore import NotFound

import datetime
import praw
from typing import Tuple, Optional
from psaw import PushshiftAPI
import environ
import uuid

env = environ.Env()
environ.Env.read_env()

reddit = praw.Reddit(
    client_id=env.str('CLIENT_ID'),
    client_secret=env.str('CLIENT_SECRET'),
    user_agent='jf_downloader',
    redirect_uri='http://localhost:8000/authorize'
)

scopes = ['identity', 'mysubreddits', 'read']
state = str(uuid.uuid4())
AUTH_URL = reddit.auth.url(scopes, state, "permanent")

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
    refresh_token = reddit.auth.authorize(auth_code) 

    request.session["refresh_token"] = refresh_token
    request.session["authenticated"] = True
    request.session["current_user"] = str(reddit.user.me())

    # Add user to database if not present.
    username = request.session.get("current_user", None)
    if not User.objects.filter(username=username).exists():
        new_user = User.objects.create(username=username)
        new_user.save()

    return redirect(reverse('downloader:search-main'))

def get_nonexistent_subreddits(include: list, exclude: list) -> list:
    """Return any nonexistent subreddits given the lists of subreddits."""
    non_existent = []
    all_subs = include + exclude
    for sub in all_subs:
        if sub == 'front' or sub == 'all':
            continue
        try:
            reddit.subreddits.search_by_name(sub, exact=True)
        except NotFound:
            non_existent.append(sub)

    return non_existent

def get_submission_data(submissions: list, sort: Optional[str] = None) -> list:
    """From the passed generator, get submission data as a list of dictionaries."""
    sub_data = []
    for sub in submissions:
        date_created = datetime.datetime.fromtimestamp(sub.created)
        permalink = 'https://www.reddit.com' + sub.permalink
        sub_data.append({'title': sub.title, 'id': sub.id, 'score': sub.score, 'permalink': permalink, \
            'url': sub.url, 'num_comments': sub.num_comments, 'date': date_created, 'selftext': sub.selftext})
    
    # Sort the data if not relying on a Reddit sorting algorithm.
    if sort == 'num_comments':
        sub_data.sort(key=sort_by_comments, reverse=True)
    elif sort == 'score':
        sub_data.sort(key=sort_by_score, reverse=True)

    return sub_data

def sort_by_comments(item):
    return item['num_comments']

def sort_by_score(item):
    return item['score']

def get_results(query: SearchQuery) -> Tuple[list, list]:
    """Determine which function is used to grab search results."""
    if query.praw_sort:             
        results = get_praw_submissions(query)
    elif query.psaw_sort:
        results = get_psaw_submissions(query)
    else:
        pass

    return results

def get_praw_submissions(query: SearchQuery) -> Tuple[list, list]:
    """Grab submissions using PRAW based on the SearchQuery object."""
    sub_list = query.subreddit.split(',')

    # Get a list of subreddits to be included and excluded from the search.
    include = [sub for sub in sub_list if not sub.startswith('!')]
    exclude = [sub.replace('!', '') for sub in sub_list if sub.startswith('!')]

    # Filter out subreddits that do not exist.
    nonexistent_subs = get_nonexistent_subreddits(include, exclude)
    include = [sub for sub in include if sub not in nonexistent_subs]
    exclude = [sub for sub in exclude if sub not in nonexistent_subs]

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
                # PRAW uses + chain subreddits
                subreddit = reddit.subreddit('+'.join(include))

            if query.praw_sort == 'hot':
                submissions = subreddit.hot(limit=lim, params={'after':last}) 
            elif query.praw_sort == 'top':
                submissions = subreddit.top(limit=lim, time_filter=query.time_filter, params={'after':last}) 
            elif query.praw_sort == 'new':
                submissions = subreddit.new(limit=lim, params={'after':last}) 
            elif query.praw_sort == 'controversial':
                submissions = subreddit.controversial(limit=lim, time_filter=query.time_filter, params={'after':last}) 
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
    return (results, nonexistent_subs)

def get_psaw_submissions(query: SearchQuery) -> Tuple[list, list]:
    """Grab submissions using PSAW based on the SearchQuery object."""

    # Drop 'all' from subreddit list if it exists (invalid for psaw)
    sub_list = query.subreddit.split(',')
    if 'all' in sub_list:
        sub_list.remove('all')

    include = [sub for sub in sub_list if not sub.startswith('!')]
    exclude = [sub.replace('!', '') for sub in sub_list if sub.startswith('!')]

    # Filter out subreddits that do not exist.
    nonexistent_subs = get_nonexistent_subreddits(include, exclude)
    include = [sub for sub in include if sub not in nonexistent_subs]
    exclude = [sub for sub in exclude if sub not in nonexistent_subs]

    # Combine the valid subreddits into an appropriately formatted string
    sub_str = ','.join(include)
    if exclude:
        sub_str += ',!' + ',!'.join(exclude)

    # Convert user input date to utc
    start_date = int(query.start_date.timestamp())
    end_date = int(query.end_date.timestamp())

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
        last = submissions_to_keep[-1].fullname

    results = get_submission_data(submissions_to_keep, sort=query.psaw_sort)
    return (results, nonexistent_subs)

def get_single_submission(id_: str):
    return reddit.submission(id=id_)