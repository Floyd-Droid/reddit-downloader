from django.test import TestCase, Client
from django.urls import reverse
from downloader.forms import (
    SearchForm
)
from downloader.models import (
    User,
    SearchQuery
)


class TestQuery(TestCase):
    fixtures = ['fixture.json']

    def setUp(self):
        self.client = Client()
        self.session = self.client.session
        self.session["authenticated"] = True
        self.session["current_user"] = "redd_spider"
        self.session.save()

    def test_create_query(self):
        response1 = self.client.get(reverse('downloader:search-main'))
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.post(
            reverse('downloader:search-main'), 
            data={'url': '', 'terms': 'cat', 'subreddit': 'pics', 'syntax': 'lucene', 'limit': 10,
                'praw_sort': 'new', 'time_filter': 'all', 'start_date': '', 
                'end_date': '', 'psaw_sort': '', 'favorite': True}
        )

        self.assertRedirects(response2, reverse('downloader:search-results', kwargs={'pk': 11}))
    
    def test_delete_queries(self):
        # All non-favorite queries are deleted.
        before_clear = User.objects.get(username='redd_spider').last_clear_datetime
        response = self.client.post(reverse('downloader:remove-queries'), data={'remove-queries': 'remove-queries', 'query_ids':'["1", "2", "3", "4", "5"]'})

        self.assertEqual(response.status_code, 200)

        # 1, 2 and 3 are favorites
        self.assertTrue(SearchQuery.objects.filter(pk__in=[1, 2, 3]).exists())
        self.assertFalse(SearchQuery.objects.filter(pk__in=[4, 5]).exists())

        after_clear = User.objects.get(username='redd_spider').last_clear_datetime
        self.assertNotEqual(before_clear, after_clear)

    
    def test_remove_favorites(self):
        # The first 3 queries in the fixture are favorites.
        response = self.client.post(reverse('downloader:remove-queries'), data={'remove-faves': 'remove-faves', 'query_ids':'["1", "2", "3"]'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SearchQuery.objects.get(pk=1).favorite)
        self.assertFalse(SearchQuery.objects.get(pk=2).favorite)
        self.assertFalse(SearchQuery.objects.get(pk=3).favorite)
    
    def test_add_favorites(self):
        # Queries 4, 5, and 6 in the fixture are not favorites.
        response = self.client.post(reverse('downloader:remove-queries'), data={'add-faves': 'add-faves', 'query_ids':'["4", "5", "6"]'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(SearchQuery.objects.get(pk=4).favorite)
        self.assertTrue(SearchQuery.objects.get(pk=5).favorite)
        self.assertTrue(SearchQuery.objects.get(pk=6).favorite)
