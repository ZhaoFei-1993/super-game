# -*- coding: UTF-8 -*-
import time
from rest_framework import serializers
from ...models import Quiz, Record, Option, Rule, Category
from time import strftime, gmtime
from decimal import Decimal
from datetime import timedelta, datetime
from users.models import User
from chat.models import Club
from api import settings
from django.db.models import Q
import pytz


class QuizSerialize(serializers.ModelSerializer):
    """
    全民竞猜题目列表
    """

    total_coin = serializers.SerializerMethodField()  # 投注总金额
    total_coin_avatar = serializers.SerializerMethodField()  # 投注总金额图标
    is_bet = serializers.SerializerMethodField()  # 是否已投注
    begin_at = serializers.SerializerMethodField()  # 是否已投注
    category = serializers.SerializerMethodField()
    is_end = serializers.SerializerMethodField()  # 是否已结束
    win_rate = serializers.SerializerMethodField()  # 胜
    planish_rate = serializers.SerializerMethodField()  # 平
    lose_rate = serializers.SerializerMethodField()  # 负
    total_people = serializers.SerializerMethodField()  # 是否已结束

    class Meta:
        model = Quiz
        fields = (
            "id", "match_name", "host_team", "host_team_avatar", "host_team_score", "guest_team", "guest_team_avatar",
            "guest_team_score", "begin_at", "total_people", "total_coin", "is_bet", "category", "is_end", "win_rate",
            "planish_rate", "lose_rate", "total_coin_avatar", "status")

    @staticmethod
    def get_begin_at(obj):
        begin_at = obj.begin_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        start = int(begin_at)
        # ok = int(time.time())-900
        return start

    def get_total_people(self, obj):
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        total_people = Record.objects.filter(quiz_id=obj.pk, roomquiz_id=roomquiz_id).count()
        return total_people

    def get_total_coin_avatar(self, obj):
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        club_info = Club.objects.get(pk=roomquiz_id)
        total_coin_avatar = club_info.coin.icon
        return total_coin_avatar

    @staticmethod
    def get_win_rate(obj):
        rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
        odds = 0
        for rule in rule_obj:
            try:
                option = Option.objects.get(rule_id=rule.pk, flag="h")
                odds = option.odds
            except Option.DoesNotExist:
                odds = 0

        return odds

    @staticmethod
    def get_planish_rate(obj):
        vv = Category.objects.get(pk=obj.category_id)
        type_id = vv.parent_id
        quiz_type = Category.objects.get(pk=type_id)
        odds = 0
        if quiz_type.name == "篮球":
            odds = ''
            return odds
        rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
        for rule in rule_obj:
            try:
                option = Option.objects.get(rule_id=rule.pk, flag="d")
                odds = option.odds
            except Option.DoesNotExist:
                odds = 0
        return odds

    @staticmethod
    def get_lose_rate(obj):
        rule_obj = Rule.objects.filter(Q(type=0) | Q(type=4), quiz_id=obj.pk)
        odds = 0
        for rule in rule_obj:
            try:
                option = Option.objects.get(rule_id=rule.pk, flag="a")
                odds = option.odds
            except Option.DoesNotExist:
                odds = 0
        return odds

    @staticmethod
    def get_is_end(obj):
        if int(obj.status) == 2:
            is_end = 1
        else:
            is_end = 0

        return is_end

    def get_total_coin(self, obj):  # 投注总金额
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        record = Record.objects.filter(quiz_id=obj.pk, roomquiz_id=roomquiz_id)
        total_coin = 0
        for coin in record:
            total_coin = total_coin + coin.bet
        total_coin = round(float(total_coin), 3)
        return total_coin

    def get_is_bet(self, obj):  # 是否已投注
        user = self.context['request'].user.id
        roomquiz_id = self.context['request'].parser_context['kwargs']['roomquiz_id']
        record_count = Record.objects.filter(user_id=user, quiz_id=obj.pk, roomquiz_id=roomquiz_id).count()
        is_vote = 0
        if record_count > 0:
            is_vote = 1
        return is_vote

    @staticmethod
    def get_category(obj):
        vv = Category.objects.get(pk=obj.category_id)
        type_id = vv.parent_id
        quiz_type = Category.objects.get(pk=type_id)
        return quiz_type.name


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

    class Meta:
        model = Record
        fields = ("id", "quiz_id", "host_team", "guest_team", "created_at", "my_option", "earn_coin", "coin_avatar",
                  "quiz_category", "bet", "coin_name")

    @staticmethod
    def get_host_team(obj):  # 主队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        host_team = quiz.host_team
        return host_team

    @staticmethod
    def get_guest_team(obj):  # 副队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        guest_team = quiz.guest_team
        return guest_team

    @staticmethod
    def get_created_at(obj):  # 时间
        years = obj.created_at.strftime('%Y')
        year = obj.created_at.strftime('%m/%d')
        time = obj.created_at.strftime('%H:%M')
        data = []
        data.append({
            'years': years,
            'year': year,
            'time': time,
        })
        return data

    @staticmethod
    def get_my_option(obj):  # 我的选项
        option_info = Option.objects.get(pk=obj.option_id)
        rule_list = Rule.objects.get(pk=option_info.rule_id)
        my_rule = rule_list.TYPE_CHOICE[int(rule_list.type)][1]
        my_option = my_rule + ":" + option_info.option + "/" + str(option_info.odds)
        data = []
        data.append({
            'my_option': my_option,  # 我的选项
            'is_right': obj.odds,  # 是否为正确答案
        })
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

    @staticmethod
    def get_earn_coin(obj):
        i = [0, 1, 2, 3]
        if int(obj.quiz.status) in i:
            earn_coin = "待开奖"
        elif int(obj.quiz.status) == 4 or int(obj.quiz.status) == 5 and Decimal(float(obj.earn_coin)) <= 0:
            earn_coin = "猜错"
        else:
            earn_coin = round(float(obj.earn_coin), 3)
        return earn_coin

    @staticmethod
    def get_quiz_category(obj):
        category_parent = obj.quiz.category.parent_id
        category = Category.objects.get(pk=category_parent)
        category_icon = category.name
        return category_icon


class QuizDetailSerializer(serializers.ModelSerializer):
    """
    竞猜详情
    """
    year = serializers.SerializerMethodField()  # 截止时间  年月日
    time = serializers.SerializerMethodField()  # 截止时间  当天时间
    # quiz_push = serializers.SerializerMethodField()  # 投注推送
    start = serializers.SerializerMethodField()  # 比赛开始时间
    status = serializers.SerializerMethodField()  # 比赛状态

    class Meta:
        model = Quiz
        fields = ("id", "host_team", "guest_team", "start", "year", "time", "status", "host_team_score",
                  "guest_team_score")

    @staticmethod
    def get_start(obj):
        begin_at = obj.begin_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        start = time.mktime(begin_at.timetuple())
        start = int(start)
        return start

    @staticmethod
    def get_status(obj):
        status = obj.status
        return status

    @staticmethod
    def get_year(obj):  # 时间
        yesterday = datetime.today() + timedelta(+1)
        yesterday_format = yesterday.strftime('%m月%d日')
        time = strftime('%m月%d日')
        year = obj.begin_at.strftime('%m月%d日')
        if time == year:
            year = year + " " + "今天"
        elif year == yesterday_format:
            year = year + " " + "明天"
        return year

    @staticmethod
    def get_time(obj):  # 时间
        year = obj.begin_at
        year = year.strftime('%H:%M')
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

    @staticmethod
    def get_my_rule(obj):
        rule = Rule.objects.get(pk=obj.rule_id)
        my_rule = rule.TYPE_CHOICE[int(rule.type)][1]
        return my_rule

    @staticmethod
    def get_bet(obj):
        bet = round(float(obj.bet), 3)
        return bet

    @staticmethod
    def get_my_option(obj):
        option = Option.objects.get(pk=obj.option_id)
        my_option = option.option
        return my_option

    @staticmethod
    def get_username(obj):
        user_info = User.objects.get(pk=obj.user_id)
        username = user_info.nickname
        user_name = str(username[0]) + "**"
        return user_name
