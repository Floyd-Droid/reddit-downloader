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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    terms = models.CharField(
        max_length=512, 
        blank=True, 
        null=True
    )
    subreddit = models.CharField(
        max_length=250, 
        blank=True, 
        null=True, 
        help_text="<br>comma separated: askreddit,askscience <br>Use ! to exclude: all,!askreddit"
    )
    syntax = models.CharField(
        max_length=11,
        choices=SYNTAX_CHOICES,
        default='lucene'
    )
    limit = models.IntegerField(default=25)
    praw_sort = models.CharField(
        max_length=13,
        choices=PRAW_SORT_CHOICES,
        blank=True,
        null=True
    )
    time_filter = models.CharField(
        max_length=5,
        choices=TIME_FILTER_CHOICES,
        blank=True,
        null=True
    )
    start_date = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="(M/D/YYYY)"
    )
    end_date = models.DateTimeField(blank=True, null=True)
    psaw_sort = models.CharField(
        max_length=18,
        choices=PSAW_SORT_CHOICES,
        blank=True,
        null=True
    )
    date_created = models.DateTimeField(auto_now=True)
    favorite = models.BooleanField(default=False)

    class Meta:
      verbose_name_plural = "Search queries"
