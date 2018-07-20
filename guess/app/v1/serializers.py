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
    closing_time = serializers.SerializerMethodField()  # 股票封盘时间
    previous_result = serializers.SerializerMethodField()  # 上期开奖指数
    previous_result_colour = serializers.SerializerMethodField()  # 上期开奖指数颜色
    last_result = serializers.SerializerMethodField()  # 上期开奖结果
    index = serializers.SerializerMethodField()  # 本期开奖指数颜色
    index_colour = serializers.SerializerMethodField()  # 本期开奖指数颜色
    rise = serializers.SerializerMethodField()  # 看涨人数
    fall = serializers.SerializerMethodField()  # 看跌人数

    class Meta:
        model = Periods
        fields = (
        "pk", "title", "periods", "closing_time", "previous_result", "previous_result_colour", "last_result",
         "index", "index_colour", "rise", "fall")

    def get_title(self, obj):  # 股票标题
        title = obj.stock.stock_id
        if self.context['request'].GET.get('language') == 'en':
            title = obj.stock.stock_id_en
        return title

    @staticmethod
    def get_last_result(obj):      # 本期开奖指数颜色
        up_and_down = obj.up_and_down
        size = obj.size
        points = obj.points
        pair = obj.pair
        if pair == None or pair == "":
            lists = str(up_and_down)+", "+str(size)+", "+str(points)
        else:
            lists = str(up_and_down)+", "+str(size)+", "+str(points)+", "+str(pair)
        return lists

    @staticmethod
    def get_rise(obj):      # 看涨人数
        number = 100
        return number

    @staticmethod
    def get_fall(obj):      # 看跌人数
        number = 100
        return number

    @staticmethod
    def get_closing_time(obj):    # 股票封盘时间
        begin_at = obj.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    @staticmethod
    def get_index(obj):      # 本期开奖指数颜色
        index_info = Index.objects.filter(periods=obj.pk).first()
        index = index_info.index_value
        return index

    @staticmethod
    def get_index_colour(obj):          # 本期开奖指数颜色
        index_info = Index.objects.filter(periods=obj.pk).first()
        index = index_info.index_value
        if index > obj.start_value:
            index_colour = 1
        elif index < obj.start_value:
            index_colour = 2
        else:
            index_colour = 3
        return index_colour

    @staticmethod
    def get_previous_result(obj):            # 上期开奖指数
        periods = int(obj.periods) - 1
        previous_period = Periods.objects.get(periods=periods)
        previous_result = previous_period.lottery_value
        return previous_result

    @staticmethod
    def get_previous_result_colour(obj):           # 上期开奖指数颜色
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
