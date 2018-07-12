# -*- coding: UTF-8 -*-
from rest_framework import serializers
from marksix.models import Play,OpenPrice,Option
from base.validators import PhoneValidator

class PlaySerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法
    """
    class Meta:
        model = Play
        fields = (
            "title","title_en","is_deleted","parent_id","id")

class OpenPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    开奖历史
    """
    class Meta:
        model=OpenPrice
        fields = (
            "issue","flat_code","special_code","animal","color",'element','closing','open','next_open'
        )

class OddsPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法赔率
    """
    class Meta:
        model=Option
        fields = (
            "option","play_id","odds"
        )