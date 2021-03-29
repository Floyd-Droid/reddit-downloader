from django.test import TestCase, Client
from django.urls import reverse
from downloader.forms import (
    SearchForm
)
from downloader.models import (
    SearchQuery
)
from downloader.tasks import (
    get_nonexistent_subreddits,
    get_forbidden_subreddits,
    get_submission_by_id,
    get_submission_data_by_url
)
from praw.models import Submission
import datetime
import environ
import praw

env = environ.Env()
environ.Env.read_env()

reddit = praw.Reddit(
    client_id=env.str('CLIENT_ID'),
    client_secret=env.str('CLIENT_SECRET'),
    user_agent='jf_downloader'
)


class TestQuery(TestCase):
    fixtures = ['fixture.json']

    def setUp(self):
        self.client = Client()
        self.session = self.client.session
        self.session["current_user"] = "redd_spider"
        self.session.save()
    
    def test_nonexistent_subreddits(self):
        include = ['askreddit', 'not-real1']
        exclude = ['askscience', 'not-real2']
        results = get_nonexistent_subreddits(include, exclude)
        self.assertEqual(['not-real1', 'not-real2'], results)
    
    def test_forbidden_subreddits(self):
        # 'centuryclub' and 'privatesubredditlist' are private subreddits
        include = ['centuryclub', 'privatesubredditlist']
        results = get_forbidden_subreddits(include)
        self.assertEqual(results, ['centuryclub', 'privatesubredditlist'])
    
    def test_get_submission_by_id(self):
        # Valid ids yield Submission objects
        result = get_submission_by_id('ecscwk')
        self.assertEqual(type(result), Submission)

        # Invalid ids yield None
        result = get_submission_by_id('invalid_id')
        self.assertEqual(result, None)
    
    def test_get_submission_data_by_url(self):
        # Valid URLs yield a list of submission data.
        result1 = get_submission_data_by_url('https://www.reddit.com/r/AskReddit/comments/ecscwk/what_free_things_online_should_everyone_take/')
        self.assertEqual(type(result1), list)

        # Invalid and NotFound URLs yield an empty list
        result2 = get_submission_data_by_url('invalid_url')
        self.assertEqual(result2, [])

        result3 = get_submission_data_by_url('https://www.reddit.com/r/AskReddit/comments/c/what_free_things_online_should_everyone_take/')
        self.assertEqual(result3, [])
    