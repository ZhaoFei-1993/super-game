# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods, Index, Record, Play, Options, Index_day
from users.models import User
import time
from api import settings
import pytz
from datetime import datetime
from chat.models import Club
from utils.functions import guess_is_seal, normalize_fraction


class PeriodsListSerialize(serializers.ModelSerializer):
    """
    期数列表序列化
    """
    date = serializers.SerializerMethodField()
    index_value = serializers.SerializerMethodField()
    is_result = serializers.SerializerMethodField()

    class Meta:
        model = Periods
        fields = ('date', 'index_value', 'is_result')

    def get_date(self, obj):
        return obj.lottery_time.strftime('%Y-%m-%d %H:%M')

    def get_index_value(self, obj):
        if obj.lottery_value is None:
            dt = '等待开奖'
            if self.context['request'].GET.get('language') == 'en':
                dt = 'Waiting for the draw'
        else:
            if len(str(obj.lottery_value).split('.')) < 2:
                dt = str(obj.lottery_value) + '0'
            else:
                dt = str(obj.lottery_value)
        return dt

    def get_is_result(self, obj):
        return obj.is_result


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
    is_seal = serializers.SerializerMethodField()  # 是否封盘

    class Meta:
        model = Stock
        fields = (
        "pk", "title", "icon", "closing_time", "previous_result", "previous_result_colour",
         "index", "index_colour", "rise", "fall", "periods_id", "result_list", "is_seal")

    def get_title(self, obj):  # 股票标题
        name = obj.name
        title = Stock.STOCK[int(name)][1]
        if self.context['request'].GET.get('language') == 'en':
            title = obj.STOCK_EN[int(name)][1]
        return title

    def get_periods_id(self, obj):  # 股票标题
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        return periods.id

    def get_rise(self, obj):      # 猜大人数
        period = Periods.objects.filter(stock_id=obj.id).order_by('-periods').first()
        count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id, options_id__in=[49,50,51,52]).count()
        return count

    def get_fall(self, obj):      # 猜小人数
        period = Periods.objects.filter(stock_id=obj.id).order_by('-periods').first()
        count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id, options_id__in=[53,54,55,56]).count()
        return count

    @staticmethod
    def get_closing_time(obj):    # 股票封盘时间
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        print("periods===========================", periods.rotary_header_time)
        begin_at = periods.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        print("begin_at======================================", begin_at)
        begin_at = time.mktime(begin_at.timetuple())
        print("begin_at======================================", begin_at)
        start = int(begin_at)
        print("start======================================", start)
        return start

    @staticmethod
    def get_is_seal(obj):    # 是否封盘
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        is_seal = guess_is_seal(periods)
        return is_seal

    @staticmethod
    def get_index(obj):      # 本期指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        index_info = Index.objects.filter(periods=periods.pk).first()
        if index_info==None or index_info=='' or periods.start_value==None or periods.start_value=='':
            index = 0
        else:
            index = index_info.index_value
        return index

    @staticmethod
    def get_index_colour(obj):          # 本期指数颜色
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        start_value = periods.start_value
        index_info = Index.objects.filter(periods=periods.pk).first()
        if index_info == None or index_info == '' or start_value==None or start_value=='':
           index_colour = 3
           return index_colour
        index = index_info.index_value
        if index > start_value:
            index_colour = 1
        elif index < start_value:
            index_colour = 2
        else:
            index_colour = 3
        return index_colour

    @staticmethod
    def get_previous_result(obj):            # 上期开奖指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        last_periods = int(periods.periods) - 1
        try:
            previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
            previous_result = previous_period.lottery_value
        except Periods.DoesNotExist:
            previous_result = ''
        except Periods.MultipleObjectsReturned:
            previous_result = ''

        return previous_result

    @staticmethod
    def get_result_list(obj):            # 上期开奖指数
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        last_periods = int(periods.periods) - 1
        if last_periods == 0:
            list =''
            return list
        previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
        if previous_period==None or previous_period=='':
            list = ''
            return list
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

        lottery_value = None
        start_value = None
        try:
            previous_period = Periods.objects.get(stock_id=obj.id, periods=last_periods)
            lottery_value = previous_period.lottery_value
            start_value = previous_period.start_value
        except Periods.DoesNotExist:
            pass
        except Periods.MultipleObjectsReturned:
            pass

        if lottery_value is None or start_value is None:
            previous_result_colour = 3
        else:
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

class GraphSerialize(serializers.ModelSerializer):
        """
        指数记录表(时分)
        """
        time = serializers.SerializerMethodField()

        class Meta:
            model = Index
            fields = ("pk", "index_value", "time")

        @staticmethod
        def get_time(obj):
            time = obj.index_time.strftime('%H:%M')
            return time

class GraphDaySerialize(serializers.ModelSerializer):
        """
        指数记录表(天)
        """
        index_day = serializers.SerializerMethodField()

        class Meta:
            model = Index_day
            fields = ("pk", "index_value", "index_day")

        @staticmethod
        def get_index_day(obj):
            index_day = obj.index_time.strftime('%m/%d')
            return index_day


class RecordSerialize(serializers.ModelSerializer):
    """
    竞猜记录表序列化
    """
    bet = serializers.SerializerMethodField()   # 下注金额
    created_at = serializers.SerializerMethodField()  # 竞猜时间
    my_option = serializers.SerializerMethodField()  # 投注选项
    coin_avatar = serializers.SerializerMethodField()   # 货币图标
    coin_name = serializers.SerializerMethodField()   # 货币昵称
    earn_coin = serializers.SerializerMethodField()  # 竞猜结果
    guess_title = serializers.SerializerMethodField()  # 股票昵称
    index = serializers.SerializerMethodField()  # 指数
    index_colour = serializers.SerializerMethodField()  # 指数颜色
    guess_result = serializers.SerializerMethodField()  # 当期结果
    is_right = serializers.SerializerMethodField()  # 是否为正确答案
    type = serializers.SerializerMethodField()  # 是否为正确答案
    stock_id = serializers.SerializerMethodField()  # 是否为正确答案

    class Meta:
        model = Record
        fields = ("id", "type", "periods_id", "stock_id", "bet", "created_at", "my_option", "coin_avatar", "coin_name", "earn_coin", "guess_title",
                  "index", "index_colour", "guess_result", "is_right")

    @staticmethod
    def get_bet(obj):  # 下注金额
        club = Club.objects.get(pk=obj.club_id)
        coin_accuracy = club.coin.coin_accuracy
        bet = normalize_fraction(obj.bets, int(coin_accuracy))
        return bet

    @staticmethod
    def get_stock_id(obj):  # 下注金额
        stock_id = obj.periods.stock_id
        return stock_id

    @staticmethod
    def get_type(obj):  # 下注金额
        if obj.earn_coin == 0 or obj.earn_coin == '':
            type = 0
        elif obj.earn_coin>0:
            type = 1
        else:
            type = 2
        return type

    @staticmethod
    def get_created_at(obj):  # 时间
        years = obj.created_at.strftime('%Y')
        year = obj.created_at.strftime('%m/%d')
        time = obj.created_at.strftime('%H:%M')
        data = [{
            'years': years,
            'year': year,
            'time': time,
        }]
        return data

    def get_my_option(self, obj):  # 我的选项
        options = Options.objects.get(pk=obj.options_id)
        play = Play.objects.get(pk=options.play.id)
        play_name =  Play.PLAY[int(play.play_name)][1]
        title = str(play_name)+"："+str(options.title)
        if self.context['request'].GET.get('language') == 'en':
            play_name = Play.PLAY_EN[int(play.play_name_en)][1]
            title = str(play_name)+"："+str(options.title_en)
        return title

    @staticmethod
    def get_coin_avatar(obj):   # 货币图标
        club_info = Club.objects.get(pk=int(obj.club_id))
        coin_avatar = club_info.coin.icon
        return coin_avatar

    @staticmethod
    def get_coin_name(obj):   # 货币昵称
        club_info = Club.objects.get(pk=int(obj.club_id))
        coin_name = club_info.coin.name
        return coin_name

    def get_earn_coin(self, obj):   # 结果
        club = Club.objects.get(pk=obj.club_id)
        if obj.earn_coin == 0 or obj.earn_coin == '':
            earn_coin = "待开奖"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Wait results"
        elif obj.earn_coin < 0:
            earn_coin = "猜错"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Guess wrong"
        else:
            earn_coin = "+" + str(normalize_fraction(obj.earn_coin, int(club.coin.coin_accuracy)))
        return earn_coin

    @staticmethod
    def get_is_right(obj):
        is_right = 0
        if obj.earn_coin > 0:
            is_right = 1
        elif obj.earn_coin < 0:
            is_right = 2
        return is_right

    def get_guess_title(self, obj):        # 股票昵称
       guess_title = Stock.STOCK[int(obj.periods.stock.name)][1]
       if self.context['request'].GET.get('language') == 'en':
           guess_title = Stock.STOCK_EN[int(obj.periods.stock.name_en)][1]
       return guess_title

    @staticmethod
    def get_index(obj):  # 本期开奖指数
        index = ''
        if obj.earn_coin > 0 or obj.earn_coin < 0:
            periods = Periods.objects.get(pk=obj.periods_id)
            index = periods.lottery_value
        return index

    @staticmethod
    def get_index_colour(obj):  # 本期指数颜色
        index_colour = ''
        if obj.earn_coin > 0 or obj.earn_coin < 0:
            periods = Periods.objects.get(pk=obj.periods_id)
            index = periods.lottery_value
            if index > periods.start_value:
                index_colour = 1
            elif index < periods.start_value:
                index_colour = 2
            else:
                index_colour = 3
        return index_colour

    def get_guess_result(self,obj):    # 开奖结果
        previous_period = Periods.objects.get(pk=obj.periods_id)
        up_and_down = previous_period.up_and_down
        if self.context['request'].GET.get('language') == 'en':
            up_and_down = previous_period.up_and_down_en
        size = previous_period.size
        if self.context['request'].GET.get('language') == 'en':
            size = previous_period.size_en
        points = previous_period.points
        pair = previous_period.pair
        if up_and_down==None or up_and_down=='':
            list = ''
        elif pair==None or pair=='':
            list = str(up_and_down)+", "+str(size)+", "+str(points)
        else:
            list = str(up_and_down)+", "+str(size)+", "+str(points)+", "+str(pair)
        return list