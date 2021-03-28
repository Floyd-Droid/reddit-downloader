from django.db import models


class User(models.Model):
    username = models.CharField(max_length=20, primary_key=True)
    last_clear_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class SearchQuery(models.Model):
    PRAW_SORT_CHOICES = (
        ('relevance', 'Relevance'),
        ('hot', 'Hot'),
        ('top', 'Top'),
        ('new', 'New'),
        ('comments', 'Comments'),
        ('controversial', 'Controversial'),
        ('rising', 'Rising'),
        ('random_rising', 'Random Rising')
    )
    PSAW_SORT_CHOICES = (
        ('created_utc', 'Date'),
        ('num_comments', 'Number of comments'),
        ('score', 'Score')
    )
    TIME_FILTER_CHOICES = (
        ('all', 'All Time'),
        ('hour', 'Past Hour'),
        ('day', 'Past 24 Hours'),
        ('month', 'Past Month'),
        ('year', 'Past Year'),
    )
    SYNTAX_CHOICES = (
        ('lucene', 'Lucene'),
        ('cloudsearch', 'Cloudsearch'),
        ('plain', 'Plain')
    )

    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=250, blank=True)
    terms = models.CharField(
        max_length=512, 
        blank=True
    )
    subreddit = models.CharField(
        max_length=250, 
        blank=True,  
        help_text="Comma separated: askreddit,askscience <br>Use ! to exclude: all,!askreddit"
    )
    syntax = models.CharField(
        max_length=11,
        choices=SYNTAX_CHOICES,
        default='lucene'
    )
    limit = models.PositiveIntegerField(default=25)
    praw_sort = models.CharField(
        max_length=13,
        choices=PRAW_SORT_CHOICES,
        blank=True
    )
    time_filter = models.CharField(
        max_length=5,
        choices=TIME_FILTER_CHOICES,
        blank=True
    )
    start_date = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="(YYYY-MM-DD [HH:MM:SS])"
    )
    end_date = models.DateTimeField(blank=True, null=True)
    psaw_sort = models.CharField(
        max_length=18,
        choices=PSAW_SORT_CHOICES,
        blank=True
    )
    date_created = models.DateTimeField(auto_now=True)
    favorite = models.BooleanField(default=False)

    class Meta:
      verbose_name_plural = "Search queries"
