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
