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
        self.fields['start_date'].input_formats = ['%m/%d/%Y']
        self.fields['end_date'].input_formats = ['%m/%d/%Y']
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
        praw_sort = cleaned_data.get('praw_sort')
        subreddit_str = cleaned_data.get('subreddit')
        subreddit_list = subreddit_str.split(',')
        if self.data.get("time_option") == 'time_filter':
            # Date range options are excluded
            cleaned_data['start_date'] = cleaned_data['end_date'] = None
            cleaned_data['psaw_sort'] = ''

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

            # front page results not possible for psaw. Remove from subreddit field.
            if 'front' in subreddit_list:
                self.add_error('subreddit', "Please either remove 'front' or select the time filter option instead of the date range.")
        return cleaned_data
