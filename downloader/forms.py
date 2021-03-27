from django import forms

from .models import (
    SearchQuery,
)


class SearchForm(forms.ModelForm):
    class Meta:
        model = SearchQuery
        exclude = (
            'date_searched',
            'user'
        )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
        self.fields['end_date'].input_formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
        self.fields['url'].label = 'URL'
        self.fields['terms'].label = 'Search terms'
        self.fields['subreddit'].label = 'Subreddit(s)'
        self.data = kwargs.get('data')

    def clean_subreddit(self):
        """Format the subreddit string: lowercase and remove whitespace."""
        cleaned_data = super(SearchForm, self).clean()
        sub = cleaned_data.get('subreddit')
        # If no subreddit is given, return 'all'
        if not sub:
            sub = 'all'
        else:
            sub = "".join(sub.split()).lower()
        return sub
    
    def clean_limit(self):
        cleaned_data = super(SearchForm, self).clean()
        lim = cleaned_data.get("limit")
        time_option = self.data.get("time_option")
        if time_option == 'time_filter' and lim > 500:
            self.add_error('limit', 'To use the standard Reddit time filter, the limit must be no greater than 500')
        elif time_option == 'date_range' and lim > 5000:
            self.add_error('limit', 'Please limit to no more than 3,000 results')
        return lim

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()
        search_option = self.data.get('search_option')
        praw_sort = cleaned_data.get('praw_sort')
        subreddit_str = cleaned_data.get('subreddit')
        subreddit_list = subreddit_str.split(',')

        # Clear all search criteria if the user gives a URL.
        if search_option == 'url':
            cleaned_data['terms'] = cleaned_data['subreddit'] = ''
            cleaned_data['time_filter'] = cleaned_data['praw_sort'] = cleaned_data['psaw_sort'] = ''
            cleaned_data['start_date'] = cleaned_data['end_date'] = None
            cleaned_data['limit'] = 1
            # if not cleaned_data.get('url'):
            #     self.add_error('url', 'Please enter a valid URL')
            return cleaned_data
        elif search_option == 'terms':
            cleaned_data['url'] = ''

        if self.data.get("time_option") == 'time_filter':
            # Date range options are excluded
            cleaned_data['start_date'] = cleaned_data['end_date'] = None
            cleaned_data['psaw_sort'] = ''

            if cleaned_data.get('time_filter') == '':
                self.add_error('time_filter', 'Please select a filter')
            if cleaned_data.get('praw_sort') == '':
                self.add_error('praw_sort', 'Please select a sort')

            # Search terms are not allowed for front page search or for certain praw sort options.
            if praw_sort in ['controversial', 'rising', 'random_rising'] or 'front' in subreddit_list:
                cleaned_data['terms'] = ''
            # A time filter won't apply to certain praw sorts.
            if praw_sort in ['hot', 'new', 'rising', 'random_rising']:
                cleaned_data['time_filter'] = ''
            # The following praw sort options require search terms
            if praw_sort in ['relevance', 'comments'] and not cleaned_data['terms']:
                self.add_error('terms', 'Search terms are required for the selected sort option')

        elif self.data.get("time_option") == 'date_range':
            cleaned_data['time_filter'] = cleaned_data['praw_sort'] = ''

            if cleaned_data.get('start_date') is None:
                self.add_error('start_date', 'Please enter a start date')
            if cleaned_data.get('end_date') is None:
                self.add_error('end_date', 'Please enter an end date')
            if cleaned_data.get('psaw_sort') == '':
                self.add_error('psaw_sort', 'Please select a sort')

            # front page results not possible for psaw. Remove from subreddit field.
            if 'front' in subreddit_list:
                self.add_error('subreddit', "Please either remove 'front' or select the time filter option instead of the date range.")
        return cleaned_data


class DownloadForm(forms.Form):

    SUBMISSION_FIELD_CHOICES = (
        ('title', 'Title'),
        ('author', 'Author'),
        ('score', 'Score'),
        ('upvote_ratio', 'Upvote ratio'),
        ('selftext', 'Selftext'),
        ('num_comments', 'Number of comments'),
        ('created_utc', 'Date created'),
        ('id', 'ID'),
        ('permalink', 'Permalink'),
        ('url', 'URL'),
        ('subreddit', 'Subreddit'),
        ('locked', 'Locked'),
        ('over_18', 'NSFW'),
        ('spoiler', 'Spoiler'),
        ('stickied', 'Stickied')
    )
    COMMENT_FIELD_CHOICES = (
        ('author', 'Author'),
        ('body', 'Text'),
        ('created_utc', 'Date created'),
        ('id', 'ID'),
        ('parent_id', 'Parent ID'),
        ('is_submitter', 'Is Submitter'),
        ('edited', 'Edited'),
        ('score', 'Score'),
        ('stickied', 'Stickied') 
    )
    COMMENT_SORT_CHOICES = (
        ('confidence', 'Best'),
        ('top', 'Top'),
        ('new', 'New'),
        ('controversial', 'Controversial'),
        ('old', 'Old'),
        ('q&a', 'Q&A')
    )

    get_submission_data = forms.BooleanField(required=False)
    get_comment_data = forms.BooleanField(required=False)
    get_external_data = forms.BooleanField(required=False)

    submission_field_options = forms.MultipleChoiceField(
        choices=SUBMISSION_FIELD_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'size':'15'})
    )
    comment_field_options = forms.MultipleChoiceField(
        choices=COMMENT_FIELD_CHOICES, 
        required=False,
        widget=forms.SelectMultiple(attrs={'size':'15'})
    )
    comment_sort_option = forms.ChoiceField(
        choices=COMMENT_SORT_CHOICES, 
        required=False
    )
    comment_limit = forms.IntegerField( 
        required=False, 
        help_text="Leave empty to retrieve all comments."
    )

    def clean(self):
        cleaned_data = super(DownloadForm, self).clean()
        # If the user checks the submission or comment box, they must also select at least one corresponding field.
        if cleaned_data.get('get_submission_data') and not cleaned_data.get('submission_field_options'):
            self.add_error('submission_field_options', 'Please select at least one field')

        comment_selected = cleaned_data.get('get_comment_data')
        limit = cleaned_data.get('comment_limit')
        if comment_selected:
            if not cleaned_data.get('comment_field_options'):
                self.add_error('comment_field_options', 'Please select at least one field')
            if limit is not None and limit < 1:
                self.add_error('comment_limit', 'Please choose a number greater than 0')
        else:
            cleaned_data['comment_field_options'] = ''
            cleaned_data['comment_limit'] = None
