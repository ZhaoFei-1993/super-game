# -*- coding: UTF-8 -*-
import time
from rest_framework import serializers
from ...models import Quiz, Record, Option, Rule
from utils.functions import surplus_date


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
    created_at = serializers.SerializerMethodField()  # 竞猜年月日
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
        option = Option.objects.filter(rule_id=obj.rule_id)
        for i in option:
            rule = Rule.objects.get(pk=i.rule_id)
            if i.id == obj.option_id:
                my_option = str(rule.type)+':'+i.option+"/"+str(i.odds)
                data = []
                data.append({
                    'my_option': my_option,
                    'is_right': i.is_right,
                })
                break
        return data


class QuizDetailSerializer(serializers.ModelSerializer):
    """
    竞猜详情
    """

    class Meta:
        model = Quiz
        fields = ("id", "host_team", "guest_team", "begin_at")

