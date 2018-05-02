# -*- coding: UTF-8 -*-
from rest_framework import serializers
from django.utils import timezone
# from datetime import datetime

from ..models import Category, Record


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    """
    竞猜分类
    """
    class Meta:
        model = Category
        fields = ("name", "parent", "is_delete")


class UserQuizSerializer(serializers.ModelSerializer):
    """
    用户竞猜记录
    """
    user_name = serializers.CharField(source='user.username')
    match_name = serializers.CharField(source='quiz.match_name')
    host_team = serializers.CharField(source='quiz.host_team')
    guest_team = serializers.CharField(source='quiz.guest_team')
    coin_icon = serializers.CharField(source='coin.icon')
    option = serializers.CharField(source='option.option')
    created_at =serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ("user_name", "match_name", "host_team", "guest_team", "coin", "coin_icon", "option", "bet", "earn_coin", "created_at")


    @staticmethod
    def get_created_at(obj):
        create_time = timezone.localtime(obj.created_at)
        created = create_time.strftime("%Y-%m-%d %H:%M:%S")
        return created