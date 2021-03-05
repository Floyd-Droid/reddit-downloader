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
