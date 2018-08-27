# -*- coding: UTF-8 -*-
import time
from datetime import timedelta, datetime
from decimal import Decimal
from time import strftime
import pytz
from django.db.models import Q
from rest_framework import serializers
from api import settings
from chat.models import Club
from users.models import User, Coin
from utils.functions import normalize_fraction
from ...models import Quiz, Record, Rule, Category, OptionOdds, ClubProfitAbroad
from utils.cache import get_cache, check_key, set_cache


class QuizSerialize(serializers.ModelSerializer):
    """
    全民竞猜题目列表
    """

    total_coin_avatar = serializers.SerializerMethodField()  # 投注总金额图标
    is_bet = serializers.SerializerMethodField()  # 是否已投注
    begin_at = serializers.SerializerMethodField()  # 是否已投注
    category = serializers.SerializerMethodField()
    is_end = serializers.SerializerMethodField()  # 是否已结束
    win_rate = serializers.SerializerMethodField()  # 胜
    planish_rate = serializers.SerializerMethodField()  # 平
    lose_rate = serializers.SerializerMethodField()  # 负
    total_people = serializers.SerializerMethodField()  # 是否已结束
    host_team = serializers.SerializerMethodField()  # 是否已结束
    guest_team = serializers.SerializerMethodField()  # 是否已结束
    match_name = serializers.SerializerMethodField()  # 是否已结束

    class Meta:
        model = Quiz
        fields = (
            "id", "match_name", "host_team", "host_team_avatar", "host_team_score", "guest_team", "guest_team_avatar",
            "guest_team_score", "begin_at", "total_people", "is_bet", "category", "is_end", "win_rate",
            "planish_rate", "lose_rate", "total_coin_avatar", "status")

    @staticmethod
    def get_begin_at(obj):
        begin_at = obj.begin_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        return start

    def get_host_team(self, obj):
        host_team = obj.host_team
        if self.context['request'].GET.get('language') == 'en':
            host_team = obj.host_team_en
            if host_team == '' or host_team is None:
                host_team = obj.host_team
        return host_team

    def get_match_name(self, obj):
        vv = Category.objects.get_one(pk=obj.category_id)
        match_name = vv.name
        if self.context['request'].GET.get('language') == 'en':
            match_name = vv.name_en
            if match_name == '' or match_name is None:
                match_name = vv.name_en
        return match_name

    def get_guest_team(self, obj):
        guest_team = obj.guest_team
        if self.context['request'].GET.get('language') == 'en':
            guest_team = obj.guest_team_en
            if guest_team == '' or guest_team is None:
                guest_team = obj.guest_team
        return guest_team

    def get_total_people(self, obj):
        """
        获取俱乐部对应竞猜投注总数
        :param obj:
        :return:
        """
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        total_people = Record.objects.get_club_quiz_bet_count(quiz_id=obj.pk, club_id=roomquiz_id)
        return total_people

    def get_total_coin_avatar(self, obj):
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        club_info = Club.objects.get_one(pk=roomquiz_id)
        coin = Coin.objects.get_one(pk=club_info.coin_id)
        return coin.icon

    def get_win_rate(self, obj):
        quiz_KEY = "QUIZ_LIST_KEY_WIN_RATE" + str(obj.pk)  # key
        win_rate = check_key(quiz_KEY)
        if win_rate == 0:
            roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
            rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
            win_rate = 0
            for rule in rule_obj:
                try:
                    option = OptionOdds.objects.get(option__rule_id=rule.pk, option__flag="h", club_id=roomquiz_id)
                    win_rate = option.odds
                except OptionOdds.DoesNotExist:
                    win_rate = 0
                set_cache(quiz_KEY, win_rate)
        return win_rate

    def get_planish_rate(self, obj):
        quiz_KEY = "QUIZ_LIST_KEY_PLANISH_RATE" + str(obj.pk)  # key
        planish_rate = check_key(quiz_KEY)
        if planish_rate == 0:
            roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']

            vv = Category.objects.get_one(pk=obj.category_id)
            type_id = vv.parent_id
            quiz_type = Category.objects.get_one(pk=type_id)
            planish_rate = 0
            if quiz_type.name == "篮球":
                odds = ''
                return odds
            rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
            for rule in rule_obj:
                try:
                    option = OptionOdds.objects.get(option__rule_id=rule.pk, option__flag="d", club_id=roomquiz_id)
                    planish_rate = option.odds
                except OptionOdds.DoesNotExist:
                    planish_rate = 0
                set_cache(quiz_KEY, planish_rate)
        return planish_rate

    def get_lose_rate(self, obj):
        quiz_KEY = "QUIZ_LIST_KEY_LOSE_RATE" + str(obj.pk)  # key
        quiz_lose_rate = check_key(quiz_KEY)
        if quiz_lose_rate == 0:
            roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']

            rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
            quiz_lose_rate = 0
            for rule in rule_obj:
                try:
                    option = OptionOdds.objects.get(option__rule_id=rule.pk, option__flag="a", club_id=roomquiz_id)
                    quiz_lose_rate = option.odds
                except OptionOdds.DoesNotExist:
                    quiz_lose_rate = 0
                set_cache(quiz_KEY, quiz_lose_rate)
        return quiz_lose_rate

    @staticmethod
    def get_is_end(obj):
        """
        比赛是否已结束
        :param obj:
        :return:
        """
        return 1 if int(obj.status) == 3 else 0

    def get_is_bet(self, obj):
        """
        是否已投注
        :param obj:
        :return:
        """
        user_id = self.context['request'].user.id
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        is_user_bet = Record.objects.get_club_quiz_bet_users(quiz_id=obj.pk, club_id=roomquiz_id, user_id=user_id)

        return 1 if is_user_bet is True else 0

    @staticmethod
    def get_category(obj):
        CATEGORY_KEY = "QUIZ_CATEGORY_KEY" + str(obj.category_id)
        quiz_type_name = check_key(CATEGORY_KEY)
        if quiz_type_name == 0:
            vv = Category.objects.get_one(pk=obj.category_id)
            type_id = vv.parent_id
            quiz_type = Category.objects.get_one(pk=type_id)
            quiz_type_name = quiz_type.name
            set_cache(CATEGORY_KEY, quiz_type_name)
        return quiz_type_name


class RecordSerialize(serializers.ModelSerializer):
    """
    竞猜记录表序列化
    """
    created_at = serializers.SerializerMethodField()  # 竞猜时间

    class Meta:
        model = Record
        fields = ("id", "quiz_id", "created_at", "odds", "earn_coin", "type", "bet", 'roomquiz_id', 'option_id')

    @staticmethod
    def get_created_at(obj):
        years = obj.created_at.strftime('%Y')
        year = obj.created_at.strftime('%m/%d')
        hour = obj.created_at.strftime('%H:%M')
        data = [{
            'years': years,
            'year': year,
            'time': hour,
        }]
        return data


class QuizDetailSerializer(serializers.ModelSerializer):
    """
    竞猜详情
    """
    year = serializers.SerializerMethodField()  # 截止时间  年月日
    time = serializers.SerializerMethodField()  # 截止时间  当天时间
    # quiz_push = serializers.SerializerMethodField()  # 投注推送
    start = serializers.SerializerMethodField()  # 比赛开始时间
    status = serializers.SerializerMethodField()  # 比赛状态
    guest_team = serializers.SerializerMethodField()  # 比赛状态
    host_team = serializers.SerializerMethodField()  # 比赛状态

    class Meta:
        model = Quiz
        fields = ("id", "host_team", "guest_team", "start", "year", "time", "status", "host_team_score",
                  "guest_team_score")

    def get_host_team(self, obj):
        host_team = obj.host_team
        if self.context['request'].GET.get('language') == 'en':
            host_team = obj.host_team_en
            if host_team == '' or host_team == None:
                host_team = obj.host_team
        return host_team

    def get_guest_team(self, obj):
        guest_team = obj.guest_team
        if self.context['request'].GET.get('language') == 'en':
            guest_team = obj.guest_team_en
            if guest_team == '' or guest_team == None:
                guest_team = obj.guest_team
        return guest_team

    @staticmethod
    def get_start(obj):
        begin_at = obj.begin_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        start = time.mktime(begin_at.timetuple())
        start = int(start)
        return start

    @staticmethod
    def get_status(obj):
        status = int(obj.status)
        return status

    def get_year(self, obj):  # 时间
        if self.context['request'].GET.get('language') == 'en':
            end_with = obj.begin_at
            new_time = end_with - timedelta(hours=12)
            years = new_time.strftime("%H:%M %p EDT")
        else:
            yesterday = datetime.today() + timedelta(+1)
            yesterday_format = yesterday.strftime('%m月%d日')
            time = strftime('%m月%d日')
            year = obj.begin_at.strftime('%m月%d日')
            years = obj.begin_at.strftime('%m月%d日')
            if time == year:
                years = year + " " + "今天"
            elif year == yesterday_format:
                years = year + " " + "明天"
        return years

    def get_time(self, obj):  # 时间
        year = obj.begin_at
        year = year.strftime('%H:%M')
        if self.context['request'].GET.get('language') == 'en':
            end_with = obj.begin_at
            new_time = end_with - timedelta(hours=12)
            year = new_time.strftime(" | %A, %b %y")
        return year

    # @staticmethod
    # def get_quiz_push(obj):
    #     """
    #     竞猜详情推送
    #     """
    #     record = Record.objects.filter(quiz_id=obj.pk)
    #     data = []
    #     for i in record:
    #         userlist = User.objects.filter(pk=i.user_id)
    #         for s in userlist:
    #             user = s.nickname
    #         rulelist = Rule.objects.get(pk=i.rule_id)
    #         my_rule = rulelist.TYPE_CHOICE[int(rulelist.type)][1]
    #         optionlist = Option.objects.get(pk=i.option_id)
    #         option = optionlist.option
    #         quiz_push = []
    #         if len(userlist) > 0:
    #             quiz_push = user[0] + "**: " + my_rule + "-" + option + " 下注" + str(i.bet) + "金币"
    #         data.append({
    #             'quiz_push': quiz_push,  # 我的选项
    #         })
    #     return data


class QuizPushSerializer(serializers.ModelSerializer):
    """
    竞猜详情推送序列化
    """
    my_rule = serializers.SerializerMethodField()  # 比赛状态
    my_option = serializers.SerializerMethodField()  # 比赛状态
    username = serializers.SerializerMethodField()  # 比赛状态
    bet = serializers.SerializerMethodField()  # 比赛状态

    class Meta:
        model = Record
        fields = ("id", "username", "my_rule", "my_option", "bet")

    def get_my_rule(self, obj):
        rule = Rule.objects.get(pk=obj.rule_id)
        my_rule = rule.tips
        if self.context['request'].GET.get('language') == 'en':
            my_rule = rule.tips_en
        return my_rule

    @staticmethod
    def get_bet(obj):
        bet = round(float(obj.bet), 3)
        return bet

    def get_my_option(self, obj):
        # option = Option.objects.get(pk=obj.option_id)
        option = OptionOdds.objects.get(pk=obj.option_id)
        my_option = option.option.option
        if self.context['request'].GET.get('language') == 'en':
            my_option = option.option.option_en
        return my_option

    @staticmethod
    def get_username(obj):
        user_info = User.objects.get(pk=obj.user_id)
        username = user_info.nickname
        user_name = str(username[0]) + "**"
        return user_name


class ClubProfitAbroadSerialize(serializers.ModelSerializer):
    """
    俱乐部收益
    """
    coin_name = serializers.SerializerMethodField()  # 俱乐部昵称
    coin_icon = serializers.SerializerMethodField()  # 货币图标
    created_at = serializers.SerializerMethodField()  # 货币图标

    class Meta:
        model = ClubProfitAbroad
        fields = ("id", "coin_name", "coin_icon", "virtual_profit", "cash_back_sum", "created_at")

    @staticmethod
    def get_coin_name(obj):
        club_info = Club.objects.get(id=obj.roomquiz_id)
        return club_info.coin.name

    @staticmethod
    def get_coin_icon(obj):
        club_info = Club.objects.get(id=obj.roomquiz_id)
        return club_info.coin.icon

    @staticmethod
    def get_created_at(obj):
        created_at = obj.created_at.strftime("%m-%d")
        return created_at
