# -*- coding: utf-8 -*-

<<<<<<< HEAD
from django.core.management.base import BaseCommand
from console.models import Address


=======
from django.core.management.base import BaseCommand, CommandError
from console.models import Address

>>>>>>> origin/master
class Command(BaseCommand):
    help = "test"

    def handle(self, *args, **options):
        for address in Address.objects.all():
            address.user = 0
<<<<<<< HEAD
            address.save()

=======
            address.save()
>>>>>>> origin/master
