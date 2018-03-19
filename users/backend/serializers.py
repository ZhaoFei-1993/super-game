# -*- coding: UTF-8 -*-
from rest_framework import serializers
import time
from ..models import CoinLock


class CoinLockSerializer(serializers.ModelSerializer):
    """
    货币锁定周期表序列化
    """
    key = serializers.SerializerMethodField()  # mapping to id

    class Meta:
        model = CoinLock
        fields = ("key", "period", "profit", "limit_start", "limit_end", "admin", "Coin", "created_at")

    @staticmethod
    def get_key(obj):
        return obj.id