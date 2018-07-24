# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods, Index, Record, Play, Options
from users.models import User
import time
from api import settings
import pytz


class StockListSerialize(serializers.ModelSerializer):
    """
    股票配置表序列化
    """
    title = serializers.SerializerMethodField()  ## 股票标题
    closing_time = serializers.SerializerMethodField()  ## 股票封盘时间
    previous_result = serializers.SerializerMethodField()  ## 上期开奖指数
    previous_result_colour = serializers.SerializerMethodField()  ## 上期开奖指数颜色
    index = serializers.SerializerMethodField()  ## 本期指数颜色
    index_colour = serializers.SerializerMethodField()  ## 本期指数颜色
    rise = serializers.SerializerMethodField()  # 看涨人数
    fall = serializers.SerializerMethodField()  # 看跌人数
    periods_id = serializers.SerializerMethodField()  # 看跌人数
    result_list = serializers.SerializerMethodField()  # 上期结果

    class Meta:
        model = Stock
        fields = (
        "pk", "title", "icon", "closing_time", "previous_result", "previous_result_colour",
         "index", "index_colour", "rise", "fall", "periods_id", "result_list")

    def get_title(self, obj):  # 股票标题
        name = obj.name
        title = Stock.STOCK[int(name)][1]
        if self.context['request'].GET.get('language') == 'en':
            title = obj.STOCK_EN[int(name)][1]
        return title

    def get_periods_id(self, obj):  # 股票标题
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        return periods.id

    def get_rise(self, obj):      # 看涨人数
        club_id = self.context['request'].GET.get('club_id')
        number = 100
        return number

    def get_fall(self, obj):      # 看跌人数
        club_id = self.context['request'].GET.get('club_id')
        number = 100
        return number

    @staticmethod
    def get_closing_time(obj):    # 股票封盘时间
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        begin_at = periods.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    @staticmethod
    def get_index(obj):      # 本期指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        index_info = Index.objects.filter(periods=periods.pk).first()
        if index_info==None or index_info=='':
            index = 0
        else:
            index = index_info.index_value
        return index

    @staticmethod
    def get_index_colour(obj):          # 本期指数颜色
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        index_info = Index.objects.filter(periods=periods.pk).first()
        if index_info == None or index_info == '':
           index_colour = 3
           return index_colour
        index = index_info.index_value
        if index > periods.start_value:
            index_colour = 1
        elif index < periods.start_value:
            index_colour = 2
        else:
            index_colour = 3
        return index_colour

    @staticmethod
    def get_previous_result(obj):            # 上期开奖指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        last_periods = int(periods.periods) - 1
        previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
        previous_result = previous_period.lottery_value
        return previous_result

    @staticmethod
    def get_result_list(obj):            # 上期开奖指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        last_periods = int(periods.periods) - 1
        previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
        up_and_down = previous_period.up_and_down
        size = previous_period.size
        points = previous_period.points
        pair = previous_period.pair
        if pair==None or pair=='':
            list = str(up_and_down)+", "+str(size)+", "+str(points)
        else:
            list = str(up_and_down)+", "+str(size)+", "+str(points)+", "+str(pair)
        return list

    @staticmethod
    def get_previous_result_colour(obj):           # 上期开奖指数颜色
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        last_periods = int(periods.periods) - 1
        previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
        lottery_value = previous_period.lottery_value
        start_value = previous_period.start_value
        if lottery_value > start_value:
            previous_result_colour = 1
        elif lottery_value < start_value:
            previous_result_colour = 2
        else:
            previous_result_colour = 3
        return previous_result_colour


class GuessPushSerializer(serializers.ModelSerializer):
        """
        竞猜详情推送序列化
        """
        my_play = serializers.SerializerMethodField()
        my_option = serializers.SerializerMethodField()
        username = serializers.SerializerMethodField()
        bet = serializers.SerializerMethodField()

        class Meta:
            model = Record
            fields = ("pk", "username", "my_play", "my_option", "bet")

        def get_my_play(self, obj):
            play = Play.objects.get(pk=obj.play_id)
            my_play = Play.PLAY[int(play.play_name)][1]
            if self.context['request'].GET.get('language') == 'en':
                my_play = Play.PLAY_EN[int(play.play_name_en)][1]
            return my_play

        @staticmethod
        def get_bet(obj):
            bet = round(float(obj.bets), 3)
            return bet

        def get_my_option(self, obj):
            option = Options.objects.get(pk=obj.options_id)
            my_option = option.title
            if self.context['request'].GET.get('language') == 'en':
                my_option = option.title_en
            return my_option

        @staticmethod
        def get_username(obj):
            user_info = User.objects.get(pk=obj.user_id)
            username = user_info.nickname
            user_name = str(username[0]) + "**"
            return user_name
