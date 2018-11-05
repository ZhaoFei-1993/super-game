from django.core.management.base import BaseCommand
from guess.models import Issues
import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        issues_list = Issues.objects.filter(left_periods_id=421)
        for issues in issues_list:
            issues.closing = issues.closing + datetime.timedelta(hours=1)
            issues.open = issues.open + datetime.timedelta(hours=1)
            issues.save()
