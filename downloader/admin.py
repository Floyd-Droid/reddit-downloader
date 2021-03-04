from django.contrib import admin

# Register your models here.

from .models import (
    SearchQuery
)

model_list = [SearchQuery]
admin.site.register(model_list)