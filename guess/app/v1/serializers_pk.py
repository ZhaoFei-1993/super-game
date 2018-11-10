# -*- coding: UTF-8 -*-
from rest_framework import serializers
from guess.models import StockPk, Issues, PlayStockPk, OptionStockPk, RecordStockPk, BetLimit


class StockPkResultListSerialize(serializers.ModelSerializer):
    """
    股指pk开奖记录
    """
    open_time = serializers.SerializerMethodField()

    class Meta:
        model = Issues
        fields = ('id', 'stock_pk_id', 'issue', 'open', 'left_stock_index',
                  'right_stock_index', 'size_pk_result', 'open_time')

    @staticmethod
    def get_open_time(obj):
        return obj.open.strftime('%Y-%m-%d %H:%M')


class StockPkRecordsListSerialize(serializers.ModelSerializer):
    """
    股指pk竞猜记录
    """
    class Meta:
        model = RecordStockPk
