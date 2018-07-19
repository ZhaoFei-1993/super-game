# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import Stock, Periods
from base.validators import PhoneValidator


class StockListSerialize(serializers.ModelSerializer):
    """
    股票配置表序列化
    """
    coin = serializers.SerializerMethodField()

    class Meta:
        model = Periods
        fields = ("title", "previous_answer")

    def get_title(self, obj):  # 货币名称
        room_title = obj.room_title
        if self.context['request'].GET.get('language') == 'en':
            room_title = obj.room_title_en
        return room_title

    def get_club_autograph(self, obj):  # 货币名称
        pass

    @staticmethod
    def get_coin(obj):  # 货币
        pass