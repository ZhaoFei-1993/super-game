# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from utils.functions import get_club_info


class Command(BaseCommand):

    def handle(self, *args, **options):
        get_club_info()

