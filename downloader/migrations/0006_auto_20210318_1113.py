# Generated by Django 3.1.6 on 2021-03-18 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('downloader', '0005_auto_20210310_0905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchquery',
            name='limit',
            field=models.PositiveIntegerField(default=25),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='praw_sort',
            field=models.CharField(blank=True, choices=[('relevance', 'Relevance'), ('hot', 'Hot'), ('top', 'Top'), ('new', 'New'), ('comments', 'Comments'), ('controversial', 'Controversial'), ('rising', 'Rising'), ('random_rising', 'Random Rising')], default='', max_length=13),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='psaw_sort',
            field=models.CharField(blank=True, choices=[('created_utc', 'Date'), ('num_comments', 'Number of comments'), ('score', 'Score')], default='', max_length=18),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='subreddit',
            field=models.CharField(blank=True, default='all', help_text='<br>comma separated: askreddit,askscience <br>Use ! to exclude: all,!askreddit', max_length=250),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='terms',
            field=models.CharField(blank=True, default='', max_length=512),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='time_filter',
            field=models.CharField(blank=True, choices=[('all', 'All Time'), ('hour', 'Past Hour'), ('day', 'Past 24 Hours'), ('month', 'Past Month'), ('year', 'Past Year')], default='', max_length=5),
            preserve_default=False,
        ),
    ]
