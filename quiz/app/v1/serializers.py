# -*- coding: UTF-8 -*-
import time
from rest_framework import serializers
from ...models import Quiz, Record, Option, Rule
from time import strftime,gmtime
from datetime import timedelta, datetime
from users.models import User
from api import settings
import pytz


class QuizSerialize(serializers.ModelSerializer):
    """
    全民竞猜题目列表
    """

    total_coin = serializers.SerializerMethodField()  # 投注总金额
    is_bet = serializers.SerializerMethodField()  # 是否已投注

    class Meta:
        model = Quiz
        fields = ("id", "match_name", "host_team", "host_team_avatar", "guest_team",
                  "guest_team_avatar", "begin_at", "total_people", "total_coin", "is_bet")

    @staticmethod
    def get_total_coin(obj):  # 投注总金额
        record = Record.objects.filter(quiz_id=obj.pk)
        total_coin=0
        for coin in record:
            total_coin=total_coin+coin.bet
        return total_coin

    def get_is_bet(self, obj):  # 是否已投注
        user = self.context['request'].user.id
        record_count = Record.objects.filter(user_id=user, quiz_id=obj.pk).count()
        is_vote = 0
        if record_count>0:
            is_vote = 1
        return is_vote



class RecordSerialize(serializers.ModelSerializer):
    """
    竞猜记录表序列化
    """
    host_team = serializers.SerializerMethodField()  # 主队
    guest_team = serializers.SerializerMethodField()  # 竞猜副队
    created_at = serializers.SerializerMethodField()  # 竞猜时间
    my_option = serializers.SerializerMethodField()  # 投注选项

    class Meta:
        model = Record
        fields = ("pk", "quiz_id", "host_team", "guest_team", "created_at", "my_option")

    @staticmethod
    def get_guest_team(obj):            # 副队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        guest_team = quiz.guest_team
        return guest_team

    @staticmethod
    def get_host_team(obj):             # 主队
        if obj.quiz_id == 0:
            return None
        quiz = Quiz.objects.get(pk=obj.quiz_id)
        host_team = quiz.host_team
        return host_team

    @staticmethod
    def get_created_at(obj):               # 时间
        year = obj.created_at.strftime('%d日%m月%Y年')
        time = obj.created_at.strftime('%H:%M')
        data = []
        data.append({
            'year': year,
            'time': time,
        })
        return data

    @staticmethod
    def get_my_option(obj):  # 我的选项
        option_list = Option.objects.filter(rule_id=obj.rule_id)
        for i in option_list:
            rule_list = Rule.objects.get(pk=i.rule_id)
            if i.id == obj.option_id:
                my_rule=rule_list.TYPE_CHOICE[int(rule_list.type)][1]
                my_option = my_rule+":"+i.option+"/"+str(i.odds)
                data = []
                data.append({
                    'my_option': my_option,          # 我的选项
                    'is_right': i.is_right,          # 是否为正确答案
                })
                break
        return data


class QuizDetailSerializer(serializers.ModelSerializer):
    """
    竞猜详情
    """
    year = serializers.SerializerMethodField()  # 截止时间  年月日
    time = serializers.SerializerMethodField()  # 截止时间  当天时间
    quiz_push = serializers.SerializerMethodField()  # 投注推送
    begin_at = serializers.SerializerMethodField()  # 比赛开始时间
    status = serializers.SerializerMethodField()  # 比赛状态

    class Meta:
        model = Quiz
        fields = ("id", "host_team", "guest_team", "begin_at", "year", "time", "status", "quiz_push")

    @staticmethod
    def get_begin_at(obj):
        begin_at = obj.begin_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        begin_at = time.mktime(begin_at.timetuple())
        return int(begin_at)

    @staticmethod
    def get_status(obj):
        status = obj.STATUS_CHOICE[int(obj.status)][1]
        return status

    @staticmethod
    def get_year(obj):               # 时间
        yesterday = datetime.today() + timedelta(+1)
        yesterday_format = yesterday.strftime('%m月%d日')
        time = strftime('%m月%d日')
        year = obj.begin_at.strftime('%m月%d日')
        if time == year:
            year = year+" "+"今天"
        elif year == yesterday_format:
            year = year+" "+"明天"
        return year

    @staticmethod
    def get_time(obj):               # 时间
        time = obj.created_at.strftime('%H:%M')
        return time

    @staticmethod
    def get_quiz_push(obj):
        """
        竞猜详情推送
        """
        record = Record.objects.filter(quiz_id=obj.pk)
        data = []
        for i in record:
            userlist = User.objects.get(pk=i.user_id)
            user = userlist.nickname
            rulelist = Rule.objects.get(pk=i.rule_id)
            my_rule = rulelist.TYPE_CHOICE[int(rulelist.type)][1]
            optionlist = Option.objects.get(pk=i.option_id)
            option = optionlist.option
            quiz_push = user[0]+"**: "+my_rule+"-"+option+" 下注"+str(i.bet)+"金币"
            data.append({
                'quiz_push': quiz_push,  # 我的选项
            })
        return data