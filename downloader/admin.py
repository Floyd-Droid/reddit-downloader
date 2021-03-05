from django.contrib import admin

# Register your models here.

from .models import (
    User,
    SearchQuery
)

model_list = [User, SearchQuery]
admin.site.register(model_list)