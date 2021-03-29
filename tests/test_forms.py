"""Test each form directly for expected validation behavior."""

from django.test import TestCase
from downloader.forms import (
    SearchForm,
    DownloadForm
)
from downloader.models import (
    User,
    SearchQuery
)
import datetime


class TestSearchForm(TestCase):
    fixtures = ['fixture.json']

    def setUp(self):
        self.start_date = datetime.datetime(2021, 3, 1)
        self.end_date = datetime.datetime(2021, 3, 5)
    
    def test_url_field(self):
        # The user must give a url if it is selected
        form1 = SearchForm(data={'url': '', 'url_select': True})
        self.assertFalse(form1.is_valid())

    def test_date_range(self):

        form1 = SearchForm(data={'terms_select': True, 'terms': '', 'subreddit': 'front,askreddit', 'syntax': 'lucene', 
            'praw_sort': 'new', 'limit': 10, 'time_filter': 'all', 'date_range_select': True, 'start_date': self.start_date, 
            'end_date': self.end_date, 'psaw_sort': 'date_created', 'favorite': True}
        )

        # front page not allowed.
        self.assertEqual(form1.errors['subreddit'], ["Please either remove 'front' or select the time filter option instead of the date range."])

        form2 = SearchForm(data={'terms_select': True, 'terms': '', 'subreddit': 'askreddit', 'syntax': 'lucene', 'limit': 10,
            'praw_sort': 'new', 'time_filter': 'day', 'date_range_select': True, 'start_date': self.start_date, 
            'end_date': self.end_date, 'psaw_sort': 'created_utc', 'favorite': True}
        )

        self.assertTrue(form2.is_valid())
        sq = form2.save(commit=False)

        # standard Reddit options are emptied
        self.assertEqual(sq.time_filter, "")
        self.assertEqual(sq.praw_sort, "")
    
    def test_time_filter(self):
        # If the time filter option is selected, the date range fields are emptied.
        form = SearchForm(data={'terms_select': True, 'terms': '', 'subreddit': 'front', 'syntax': 'lucene', 'praw_sort': 'new', 
            'limit': 10, 'time_filter_select': True, 'time_filter': 'all', 'start_date': self.start_date, 
            'end_date': self.end_date, 'psaw_sort': 'created_utc', 'favorite': True}
        )
        self.assertTrue(form.is_valid())
        sq = form.save(commit=False)

        self.assertEqual(sq.start_date, None)
        self.assertEqual(sq.end_date, None)
        self.assertEqual(sq.psaw_sort, "")

    def test_ignore_terms(self):
        """Ensure the search terms field is set to empty string if a certain praw sort is selected"""
        sort_options = ['controversial', 'rising', 'random_rising']
        for opt in sort_options:
            form = SearchForm(data={'terms_select': True, 'terms': 'test', 'subreddit': 'askreddit', 'syntax': 'lucene', 
                'praw_sort': opt, 'limit': 10, 'time_filter_select': True, 'time_filter': 'all', 'start_date': '', 
                'end_date': '', 'psaw_sort': '', 'favorite': True}
            )
            sq = form.save(commit=False)
            self.assertEqual(sq.terms, "")

    
    def test_ignore_time_filter(self):
        """
        Ensure the time_filter field is set to an empty string if 
        (1) There are no search terms, and 
        (2) A certain praw sort is selected.
        """
        sort_options = ['hot', 'new', 'rising', 'random_rising']
        for opt in sort_options:
            form = SearchForm(data={'terms_select': True, 'terms': '', 'subreddit': 'askreddit', 'syntax': 'lucene', 
                'praw_sort': opt, 'limit': 10, 'time_filter_select': True, 'time_filter': 'all', 'start_date': '', 
                'end_date': '', 'psaw_sort': '', 'favorite': True}
            )
            sq = form.save(commit=False)
            self.assertEqual(sq.time_filter, "")
        
    def test_required_search_terms(self): 
        """Ensure that search terms are required if a certain praw sort option is selected"""
        sort_options = ['relevance', 'comments']
        for opt in sort_options:
            form = SearchForm(data={'terms': '', 'subreddit': 'askreddit', 'syntax': 'lucene', 
                'praw_sort': opt, 'limit': 10, 'time_filter_select': True, 'time_filter': 'all', 'start_date': '', 
                'end_date': '', 'psaw_sort': '', 'favorite': True}
            )
            self.assertEqual(form.errors['terms'], ['Search terms are required for the selected sort option'])

    def test_empty_subreddit(self):
        """An empty subreddit field should be replaced with 'all'."""
        form = SearchForm(data={'terms_select': True, 'terms': '', 'subreddit': '', 'syntax': 'lucene', 'praw_sort': 'new', 
            'limit': 10, 'time_filter_select': True, 'time_filter': 'all', 'start_date': '', 'end_date': '', 'psaw_sort': '', 
            'favorite': True, 'time_option': 'time_filter'}
        )
        sq = form.save(commit=False)
        self.assertEqual(sq.subreddit, 'all')


class TestDownloadForm(TestCase):
    fixtures = ['fixture.json']
    
    def test_requirements(self):
        form1 = DownloadForm(data={'get_submission_data': True, 'get_comment_data': True, 'comment_limit': 0})

        # Fields must be selected
        self.assertEqual(form1.errors['submission_field_options'], ['Please select at least one field'])
        self.assertEqual(form1.errors['comment_field_options'], ['Please select at least one field'])

        # The limit cannot be less than 0
        self.assertEqual(form1.errors['comment_limit'], ['Please choose a number greater than 0'])
