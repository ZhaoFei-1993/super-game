# -*- coding: UTF-8 -*-
from rest_framework import serializers
from datetime import datetime
from utils.functions import number_time_judgment
from utils.cache import get_cache, set_cache, delete_cache
from dragon_tiger.models import BetLimit