# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods, Index
import time
from api import settings
import pytz


class PeriodsListSerialize(serializers.ModelSerializer):
    """
    股票配置表序列化
    """
    title = serializers.SerializerMethodField()  # 股票标题
    rotary_header_time = serializers.SerializerMethodField()  # 股票封盘时间
    previous_result = serializers.SerializerMethodField()  # 上期开奖指数
    previous_result_colour = serializers.SerializerMethodField()  # 上期开奖指数颜色
    index = serializers.SerializerMethodField()  # 上期开奖指数颜色
    index_colour = serializers.SerializerMethodField()  # 上期开奖指数颜色

    class Meta:
        model = Periods
        fields = (
            "title", "periods", "rotary_header_time", "previous_result", "previous_result_colour", "up_and_down",
            "size", "points", "pair", "index", "index_colour")

    def get_title(self, obj):  # 货币名称
        title = obj.stock.stock_id
        if self.context['request'].GET.get('language') == 'en':
            title = obj.stock.stock_id_en
        return title

    @staticmethod
    def get_rotary_header_time(obj):
        begin_at = obj.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    @staticmethod
    def get_index(obj):
        begin_at = obj.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    @staticmethod
    def get_index_colour(obj):
        begin_at = obj.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    @staticmethod
    def get_previous_result(obj):
        periods = int(obj.periods) - 1
        previous_period = Periods.objects.get(periods=periods)
        previous_result = previous_period.lottery_value
        return previous_result


    @staticmethod
    def get_previous_result_colour(obj):
        periods = int(obj.periods) - 1
        previous_period = Periods.objects.get(periods=periods)
        lottery_value = previous_period.lottery_value
        start_value = previous_period.start_value
        if lottery_value > start_value:
            previous_result_colour = 1
        elif lottery_value < start_value:
            previous_result_colour = 2
        else:
            previous_result_colour = 3
        return previous_result_colour
