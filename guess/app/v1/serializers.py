# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods, Index, Record, Play, Options, Index_day
from users.models import User
import time
from api import settings
import pytz
from datetime import datetime
from chat.models import Club
from utils.functions import guess_is_seal, normalize_fraction, get_club_info
from utils.cache import get_cache, set_cache


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
    # stock_id = serializers.SerializerMethodField()  # 股票pk
    # icon = serializers.SerializerMethodField()  # 股票图标
    # title = serializers.SerializerMethodField()  # 股票标题
    closing_time = serializers.SerializerMethodField()  # 股票封盘时间
    # lottery_time = serializers.SerializerMethodField()  # 股票开奖时间
    # previous_result = serializers.SerializerMethodField()  # 上期开奖指数
    # previous_result_colour = serializers.SerializerMethodField()  # 上期开奖指数颜色
    # index = serializers.SerializerMethodField()  # 本期指数颜色
    # index_colour = serializers.SerializerMethodField()  # 本期指数颜色
    # rise = serializers.SerializerMethodField()  # 看涨人数
    # fall = serializers.SerializerMethodField()  # 看跌人数
    periods_id = serializers.SerializerMethodField()  # 看跌人数
    # result_list = serializers.SerializerMethodField()  # 上期结果

    # is_seal = serializers.SerializerMethodField()  # 是否封盘

    class Meta:
        model = Periods
        fields = ("closing_time", "periods_id")

    # def get_stock_id(self, obj):
    #     return obj.stock_id

    # def get_title(self, obj):  # 股票标题
    #     name = obj.stock.name
    #     title = Stock.STOCK[int(name)][1]
    #     if self.context['request'].GET.get('language') == 'en':
    #         title = Stock.STOCK_EN[int(name)][1]
    #     return title
    #
    # def get_icon(self, obj):
    #     return obj.stock.icon

    def get_periods_id(self, obj):  # 股票标题
        # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        # rise = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
        #                               options_id__in=[49, 50, 51, 52]).count()           # 看涨人数
        # rise = Record.objects.filter(periods_id=obj.id, options__play__stock_id=obj.stock_id,
        #                              options_id__in=[1, 2, 3, 4]).count()  # 看涨人数
        # fall = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
        #                               options_id__in=[53, 54, 55, 56]).count()         # 看跌人数
        # fall = Record.objects.filter(periods_id=obj.id, options__play__stock_id=obj.stock_id,
        #                              options_id__in=[5, 6, 7, 8]).count()  # 看跌人数

        # 缓存看大看小人数
        key_record_bet_count = 'record_stock_bet_count' + '_' + str(obj.id)
        record_stock_bet_count = get_cache(key_record_bet_count)

        is_seal = obj.is_seal  # 是否封盘

        data = {
            obj.stock_id: {
                "period_id": obj.id,
                "rise": record_stock_bet_count['rise'],
                "is_seal": is_seal,
                "fall": record_stock_bet_count['fall'],
            }
        }
        return data

    # # @staticmethod
    # def get_is_seal(obj):  # 是否封盘
    #     periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     is_seal = guess_is_seal(periods)
    #     return is_seal

    # @staticmethod
    # def get_index(obj):  # 本期指数
    #     periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     index_info = Index.objects.filter(periods=periods.pk).first()
    #     if index_info == None or index_info == '' or periods.start_value == None or periods.start_value == '':
    #         index = 0
    #     else:
    #         index = index_info.index_value
    #     return index

    # def get_rise(self, obj):  # 猜大人数
    #     period = Periods.objects.filter(stock_id=obj.id).order_by('-periods').first()
    #     # count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
    #     #                               options_id__in=[49, 50, 51, 52]).count()
    #     count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
    #                                   options_id__in=[1, 2, 3, 4]).count()
    #     return count
    #
    # def get_fall(self, obj):  # 猜小人数
    #     period = Periods.objects.filter(stock_id=obj.id).order_by('-periods').first()
    #     # count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
    #     #                               options_id__in=[53, 54, 55, 56]).count()
    #     count = Record.objects.filter(periods_id=period.id, options__play__stock_id=obj.id,
    #                                   options_id__in=[5, 6, 7, 8]).count()
    #     return count

    @staticmethod
    def get_closing_time(obj):  # 股票封盘时间
        # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        begin_at = obj.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        created_at = obj.lottery_time.astimezone(pytz.timezone(settings.TIME_ZONE))
        created_at = time.mktime(created_at.timetuple())
        start_at = int(created_at)
        day = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lottery_time = obj.lottery_time.strftime('%Y-%m-%d %H:%M:%S')  # 开奖时间
        start_time = obj.start_time.strftime('%Y-%m-%d %H:%M:%S')  # 开始下注时间
        rotary_header_time = obj.rotary_header_time.strftime('%Y-%m-%d %H:%M:%S')  # 封盘时间
        status = -1
        if start_time < day < rotary_header_time:
            status = 0  # 开始投注
        elif obj.is_seal is True and obj.is_result is not True and datetime.now() < obj.lottery_time:
            status = 1  # 封盘中
        elif datetime.now() > obj.lottery_time and obj.is_result is not True:
            status = 2  # 结算中
        elif obj.is_result is True:
            status = 3  # 已开奖
        data = {
            obj.stock_id: {
                "start": start,
                "start_at": start_at,
                "status": status
            }
        }
        return data

    # @staticmethod
    # def get_lottery_time(obj):    # 股票开奖时间
    #     periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     begin_at = periods.lottery_time.astimezone(pytz.timezone(settings.TIME_ZONE))
    #     begin_at = time.mktime(begin_at.timetuple())
    #     start = int(begin_at)
    #     return start

    # @staticmethod
    # def get_index_colour(obj):  # 本期指数颜色
    #     # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     start_value = obj.start_value
    #     index_info = Index.objects.filter(periods_id=obj.pk).first()
    #     if index_info == None or index_info == '' or start_value == None or start_value == '':
    #         index_colour = 4
    #         return index_colour
    #     index = index_info.index_value
    #     if index > start_value:
    #         index_colour = 1
    #     elif index < start_value:
    #         index_colour = 2
    #     else:
    #         index_colour = 3
    #     return index_colour

    # @staticmethod
    # def get_previous_result(obj):  # 上期开奖指数
    #     # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     last_periods = int(obj.periods) - 1
    #     try:
    #         previous_period = Periods.objects.get(stock_id=obj.stock.id, periods=last_periods)
    #         previous_result = previous_period.lottery_value
    #     except Periods.DoesNotExist:
    #         previous_result = ''
    #     except Periods.MultipleObjectsReturned:
    #         previous_result = ''
    #
    #     return previous_result
    #
    # @staticmethod
    # def get_result_list(obj):  # 上期开奖指数
    #     # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     last_periods = int(obj.periods) - 1
    #     if last_periods == 0:
    #         list = ''
    #         return list
    #     previous_period = Periods.objects.get(stock_id=obj.stock.id, periods=last_periods)
    #     if previous_period is None or previous_period == '':
    #         list = ''
    #         return list
    #     up_and_down = previous_period.up_and_down
    #     size = previous_period.size
    #     points = previous_period.points
    #     pair = previous_period.pair
    #     if pair is None or pair == '':
    #         # list = str(up_and_down)+", "+str(size)+", "+str(points)
    #         list = str(size) + "、  " + str(points)
    #     else:
    #         list = str(size) + "、  " + str(points) + "、  " + str(pair)
    #     return list
    #
    # @staticmethod
    # def get_previous_result_colour(obj):  # 上期开奖指数颜色
    #     # periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
    #     last_periods = int(obj.periods) - 1
    #
    #     lottery_value = None
    #     start_value = None
    #     try:
    #         previous_period = Periods.objects.get(stock_id=obj.stock.id, periods=last_periods)
    #         lottery_value = previous_period.lottery_value
    #         start_value = previous_period.start_value
    #     except Periods.DoesNotExist:
    #         pass
    #     except Periods.MultipleObjectsReturned:
    #         pass
    #
    #     if lottery_value is None or start_value is None:
    #         previous_result_colour = 3
    #     else:
    #         if lottery_value > start_value:
    #             previous_result_colour = 1
    #         elif lottery_value < start_value:
    #             previous_result_colour = 2
    #         else:
    #             previous_result_colour = 3
    #     return previous_result_colour


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
    bet = serializers.SerializerMethodField()  # 下注金额
    created_at = serializers.SerializerMethodField()  # 竞猜时间
    # my_option = serializers.SerializerMethodField()  # 投注选项
    coin_avatar = serializers.SerializerMethodField()  # 货币图标
    coin_name = serializers.SerializerMethodField()  # 货币昵称
    earn_coin_result = serializers.SerializerMethodField()  # 竞猜结果
    earn_coin = serializers.SerializerMethodField()
    # guess_title = serializers.SerializerMethodField()  # 股票昵称
    # index = serializers.SerializerMethodField()  # 指数
    # index_colour = serializers.SerializerMethodField()  # 指数颜色
    # guess_result = serializers.SerializerMethodField()  # 当期结果
    is_right = serializers.SerializerMethodField()  # 是否为正确答案
    type = serializers.SerializerMethodField()  # 是否为正确答案
    # stock_id = serializers.SerializerMethodField()
    obj = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ("id", "user_id", "type", "periods_id", "bet", "created_at", "coin_avatar",
                  "coin_name", "earn_coin", "earn_coin_result", "is_right", "obj")

    @staticmethod
    def get_obj(obj):
        return obj

    # @staticmethod
    # def get_bet(obj):  # 下注金额
    #     coin_accuracy = obj.club.coin.coin_accuracy
    #     bet = normalize_fraction(obj.bets, int(coin_accuracy))
    #     return bet
    @staticmethod
    def get_bet(obj):  # 下注金额
        cache_club_value = get_club_info()
        coin_accuracy = cache_club_value[obj.club_id]['coin_accuracy']
        bet = normalize_fraction(obj.bets, int(coin_accuracy))
        return bet

    # @staticmethod
    # def get_stock_id(obj):
    #     stock_id = obj.periods.stock_id
    #     return stock_id

    @staticmethod
    def get_type(obj):  # 下注金额
        if obj.earn_coin == 0 or obj.earn_coin == '':
            type = 0
        elif obj.earn_coin > 0:
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

    # def get_my_option(self, obj):  # 我的选项
    #     play_name = obj.play.PLAY[int(obj.play.play_name)][1]
    #     title = str(play_name) + "：" + str(obj.options.title)
    #     if self.context['request'].GET.get('language') == 'en':
    #         play_name = obj.play.PLAY_EN[int(obj.play.play_name_en)][1]
    #         title = str(play_name) + "：" + str(obj.options.title_en)
    #     return title

    # @staticmethod
    # def get_coin_avatar(obj):  # 货币图标
    #     coin_avatar = obj.club.coin.icon
    #     return coin_avatar
    @staticmethod
    def get_coin_avatar(obj):  # 货币图标
        cache_club_value = get_club_info()
        coin_avatar = cache_club_value[obj.club_id]['coin_icon']
        return coin_avatar

    # @staticmethod
    # def get_coin_name(obj):  # 货币昵称
    #     coin_name = obj.club.coin.name
    #     return coin_name
    @staticmethod
    def get_coin_name(obj):  # 货币昵称
        cache_club_value = get_club_info()
        coin_name = cache_club_value[obj.club_id]['coin_name']
        return coin_name

    def get_earn_coin_result(self, obj):  # 结果
        cache_club_value = get_club_info()
        coin_accuracy = cache_club_value[obj.club_id]['coin_accuracy']

        if obj.earn_coin == 0 or obj.earn_coin == '':
            earn_coin = "待开奖"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Wait results"
        elif obj.earn_coin < 0:
            earn_coin = "猜错"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Guess wrong"
        else:
            earn_coin = "+" + str(normalize_fraction(obj.earn_coin, int(coin_accuracy)))
        return earn_coin

    @staticmethod
    def get_earn_coin(obj):  # 下注金额
        return obj.earn_coin

    @staticmethod
    def get_is_right(obj):
        is_right = 0
        if obj.earn_coin > 0:
            is_right = 1
        elif obj.earn_coin < 0:
            is_right = 2
        return is_right

    # def get_guess_title(self, obj):  # 股票昵称
    #     guess_title = Stock.STOCK[int(obj.periods.stock.name)][1]
    #     if self.context['request'].GET.get('language') == 'en':
    #         guess_title = Stock.STOCK_EN[int(obj.periods.stock.name_en)][1]
    #     return guess_title

    # @staticmethod
    # def get_index(obj):  # 本期开奖指数
    #     index = ''
    #     if obj.earn_coin > 0 or obj.earn_coin < 0:
    #         index = obj.periods.lottery_value
    #     return index
    #
    # @staticmethod
    # def get_index_colour(obj):  # 本期指数颜色
    #     index_colour = ''
    #     if obj.earn_coin > 0 or obj.earn_coin < 0:
    #         index = obj.periods.lottery_value
    #         if index > obj.periods.start_value:
    #             index_colour = 1
    #         elif index < obj.periods.start_value:
    #             index_colour = 2
    #         else:
    #             index_colour = 3
    #     return index_colour

    # def get_guess_result(self, obj):  # 开奖结果
    #     up_and_down = obj.periods.up_and_down
    #     if self.context['request'].GET.get('language') == 'en':
    #         up_and_down = obj.periods.up_and_down_en
    #     size = obj.periods.size
    #     if self.context['request'].GET.get('language') == 'en':
    #         size = obj.periods.size_en
    #     points = obj.periods.points
    #     pair = obj.periods.pair
    #     if up_and_down == None or up_and_down == '':
    #         list = ''
    #     elif pair == None or pair == '':
    #         list = str(size) + "、 " + str(points)
    #     else:
    #         list = str(size) + "、 " + str(points) + "、 " + str(pair)
    #     return list
