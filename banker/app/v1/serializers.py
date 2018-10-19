# -*- coding: UTF-8 -*-
from rest_framework import serializers
from chat.models import Club, ClubRule

class ClubRuleSerialize(serializers.ModelSerializer):
    """
    玩法序列化
    """
    name = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()

    class Meta:
        model = ClubRule
        fields = ("id", "name", "number", "icon")
