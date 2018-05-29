# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from console.models import Address

class Command(BaseCommand):
    help = "test"

    def handle(self, *args, **options):
        for address in Address.objects.all():
            address.user = 0
            address.save()