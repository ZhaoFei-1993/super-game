# -*- coding: UTF-8 -*-
from base.backend import FormatListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from django.db import connection
from api.settings import REST_FRAMEWORK
from django.db import transaction

from mptt.utils import get_cached_trees
from rest_framework import status
from utils.functions import convert_localtime
from rest_framework.reverse import reverse
from django.http import HttpResponse
import json

