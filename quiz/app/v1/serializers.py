# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Quiz, Record
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
        bet = Record.objects.filter(user_id=user, quiz_id=obj.pk)
        is_vote = 0
        if len(bet)>0:
            is_vote = 1
        return is_vote



