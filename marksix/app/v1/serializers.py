# -*- coding: UTF-8 -*-
from rest_framework import serializers
from marksix.models import Play, OpenPrice, Option, SixRecord, Number
from base.validators import PhoneValidator
from chat.models import Club
from datetime import datetime


class PlaySerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法
    """
    title = serializers.SerializerMethodField()  # 玩法名称

    class Meta:
        model = Play
        fields = (
            "id", 'title')

    def get_title(self, obj):
        title = obj.title
        if self.context['request'].GET.get('language') == 'en':
            title = obj.title_en
        return title


class OpenPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    开奖历史
    """

    # animal = serializers.SerializerMethodField()  # 货币名称

    class Meta:
        model = OpenPrice
        fields = (
            "issue", "flat_code", "special_code", "animal", "color", 'element', 'closing', 'open', 'next_open','starting'
        )

        # def get_animal(self, obj):
        #     animal_index = obj.animal


class OddsPriceSerializer(serializers.HyperlinkedModelSerializer):
    """
    玩法赔率
    """

    class Meta:
        model = Option
        fields = (
            "option", "play_id", "odds"
        )


class RecordSerializer(serializers.HyperlinkedModelSerializer):
    """
    下注
    """
    coin_name = serializers.SerializerMethodField()  # 货币名称
    option_name = serializers.SerializerMethodField()  # 玩法名称
    created_time = serializers.SerializerMethodField()  # 下注时间处理，保留到分钟
    earn = serializers.SerializerMethodField()  # 投注状态，下注结果，下注正确，错误，或者挣钱
    content = serializers.SerializerMethodField() # 下注内容
    coin_avartar = serializers.SerializerMethodField() # 币种图标


    class Meta:
        model = SixRecord
        fields = (
            "bet", "bet_coin", "status", "created_time", "issue",
            "content", 'coin_name', 'option_name', 'earn','coin_avartar'
        )

    def get_content(self,obj):
        play = obj.play
        option_id = obj.option_id
        res = obj.content
        language = self.context['request'].GET.get('language','zh')
        res_list = res.split(',')
        if play != '1' and option_id == '':
            content_list = []
            for pk in res_list:
                if language == 'zh':
                    title = Option.objects.get(id=pk).option
                else:
                    title = Option.objects.get(id=pk).option_en
                content_list.append(title)
            res = ','.join(content_list)
        return res

    def get_coin_name(self, obj):
        club_id = obj.club_id
        coin_name = Club.objects.get(id=club_id).coin.name
        return coin_name

    def get_option_name(self, obj):
        option_id = obj.option_id
        if option_id:
            res = Option.objects.get(id=option_id)
            three_to_two = '三中二'
            option_name = res.option
            if three_to_two in option_name:
                option_name = three_to_two
            if self.context['request'].GET.get('language') == 'en':
                three_to_two = 'Three Hit Two'
                option_name = res.option_en
                if three_to_two in option_name:
                    option_name = three_to_two
        else:
            option_name = obj.play.title
            if self.context['request'].GET.get('language') == 'en':
                option_name = obj.play.title_en

        return option_name

    def get_created_time(self, obj):
        created_time = obj.created_at.strftime('%Y-%m-%d %H:%M')
        return created_time

    def get_earn(self, obj):
        language = 'zh'
        if self.context['request'].GET.get('language') == 'en':
            language = 'en'
        result = obj.status
        earn_coin = obj.earn_coin
        if result == '0':
            if language == 'zh':
                earn = '待开奖'
            else:
                earn = 'AWAIT OPEN'
        else:
            if earn_coin == 0:
                earn = 'GUESSING ERROR'
            else:
                earn = '+' + str(int(earn_coin))

        return earn

    def get_coin_avartar(self,obj):
        club_id = obj.club_id
        coin_avartar = Club.objects.get(id=club_id).coin.icon
        return coin_avartar


class ColorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Number
        fields = (
            'num', 'color'
        )
