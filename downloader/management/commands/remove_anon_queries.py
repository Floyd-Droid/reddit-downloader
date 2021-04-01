from django.core.management.base import BaseCommand, CommandError
from downloader.models import SearchQuery
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Deletes SearchQuery objects created by anonymous users which are older than one day.'

    def handle(self):
        try:
            SearchQuery.objects.filter(user=None, date_created__lte=datetime.now()-timedelta(days=1)).delete()
        except:
            self.stdout.write(self.style.ERROR('Failed to delete stale queries.'))
            return

        self.stdout.write(self.style.SUCCESS('Successfully deleted stale queries.'))
        return
