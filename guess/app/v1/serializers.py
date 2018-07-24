# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods, Index, Record, Play, Options
from users.models import User
import time
from api import settings
import pytz
from datetime import datetime
from utils.functions import guess_is_seal, normalize_fraction


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
    def get_is_seal(obj):    # 股票封盘时间
        periods = Periods.objects.filter(stock_id=obj.id).order_by("-periods").first()
        is_seal = guess_is_seal(periods)
        return is_seal

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


class RecordSerialize(serializers.ModelSerializer):
    """
    竞猜记录表序列化
    """
    host_team = serializers.SerializerMethodField()  # 主队
    guest_team = serializers.SerializerMethodField()  # 竞猜副队
    created_at = serializers.SerializerMethodField()  # 竞猜时间
    my_option = serializers.SerializerMethodField()  # 投注选项
    coin_avatar = serializers.SerializerMethodField()  # 投注选项
    coin_name = serializers.SerializerMethodField()  # 投注选项
    earn_coin = serializers.SerializerMethodField()  # 竞猜结果
    quiz_category = serializers.SerializerMethodField()  # 竞猜结果
    bets = serializers.SerializerMethodField()  # 竞猜结果

    class Meta:
        model = Record
        fields = ("id", "quiz_id", "host_team", "guest_team", "created_at", "my_option", "earn_coin", "coin_avatar",
                  "quiz_category", "type", "bets", "coin_name")

    @staticmethod
    def get_bets(obj):  # 主队
        club = Club.objects.get(pk=obj.roomquiz_id)
        coin_accuracy = club.coin.coin_accuracy
        bet = normalize_fraction(obj.bet, int(coin_accuracy))
        return bet

    def get_host_team(self, obj):  # 主队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        host_team = quiz.host_team
        if self.context['request'].GET.get('language') == 'en':
            host_team = quiz.host_team_en
            if host_team == '' or host_team == None:
                host_team = quiz.host_team
        return host_team

    def get_guest_team(self, obj):  # 副队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        guest_team = quiz.guest_team
        if self.context['request'].GET.get('language') == 'en':
            guest_team = quiz.guest_team_en
            if guest_team == '' or guest_team == None:
                guest_team = quiz.guest_team
        return guest_team

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
        # option_info = Option.objects.get(pk=obj.option_id)
        options = OptionOdds.objects.get(pk=obj.option_id)

        rule_list = Rule.objects.get(pk=options.option.rule_id)
        my_rule = rule_list.tips
        option = options.option.option
        if self.context['request'].GET.get('language') == 'en':
            my_rule = rule_list.tips_en
            if my_rule == '' or my_rule == None:
                my_rule = rule_list.tips
            option = options.option.option_en
            if option == '' or option == None:
                option = options.option.option
        my_option = my_rule + ":" + option + "/" + str(
            normalize_fraction(obj.odds, 2))

        data = [{
            'my_option': my_option,  # 我的选项
            'is_right': options.option.is_right,  # 是否为正确答案
        }]
        return data

    @staticmethod
    def get_coin_avatar(obj):
        club_info = Club.objects.get(pk=int(obj.roomquiz_id))
        coin_avatar = club_info.coin.icon
        return coin_avatar

    @staticmethod
    def get_coin_name(obj):
        club_info = Club.objects.get(pk=int(obj.roomquiz_id))
        coin_name = club_info.coin.name
        return coin_name

    def get_earn_coin(self, obj):
        club = Club.objects.get(pk=obj.roomquiz_id)
        i = [0, 1, 2, 3]
        if int(obj.quiz.status) in i:
            earn_coin = "待开奖"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Wait results"
        elif int(obj.quiz.status) == 4 or int(obj.quiz.status) == 5 and Decimal(float(obj.earn_coin)) <= 0:
            earn_coin = "猜错"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Guess wrong"
        else:
            earn_coin = "+" + str(normalize_fraction(obj.earn_coin, int(club.coin.coin_accuracy)))
        return earn_coin

    @staticmethod
    def get_quiz_category(obj):
        category_parent = obj.quiz.category.parent_id
        category = Category.objects.get(pk=category_parent)
        category_icon = category.name
        return category_icon

