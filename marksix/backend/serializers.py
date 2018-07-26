# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ..models import Play, Option, OpenPrice, Number, Animals
from datetime import datetime


class PlayBackendSerializer(serializers.ModelSerializer):
    """
    玩法序列化
    """

    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Play
        fields = ('id', 'title', 'title_en', 'is_deleted', 'created_at')

    @staticmethod
    def get_created_at(obj):
        created_at = obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else ''
        return created_at


class OptionBackendSerializer(serializers.ModelSerializer):
    """
    选项序列化
    """
    created_at = serializers.SerializerMethodField()
    play_title = serializers.CharField(source='play.title')

    class Meta:
        model = Option
        fields = ('id', 'option', 'option_en', 'play_id', 'play_title', 'odds', 'is_deleted', 'created_at')

    @staticmethod
    def get_created_at(obj):
        created_at = obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else ''
        return created_at


class OpenPriceBackendSerializer(serializers.ModelSerializer):
    """
    开奖结果
    """
    closing = serializers.SerializerMethodField()
    open = serializers.SerializerMethodField()
    next_open = serializers.SerializerMethodField()
    is_timeout = serializers.SerializerMethodField()  # 是否到时
    animal = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    element = serializers.SerializerMethodField()
    starting = serializers.SerializerMethodField()

    class Meta:
        model = OpenPrice
        fields = (
        'id', 'issue', 'flat_code', 'special_code', 'animal', 'color', 'element', 'closing', 'starting', 'open',
        'next_open', 'is_open', 'is_timeout')

    @staticmethod
    def get_animal(obj):
        if obj.animal:
            for x in Animals.ANIMAL_CHOICE:
                if x[0] == int(obj.animal):
                    return x[1]
        return ''

    @staticmethod
    def get_color(obj):
        if obj.color:
            for x in Number.WAVE_CHOICE:
                if x[0] == int(obj.color):
                    return x[1]
        return ''

    @staticmethod
    def get_element(obj):
        if obj.element:
            for x in Number.ELEMENT_CHOICE:
                if x[0] == int(obj.color):
                    return x[1]
        return ''

    @staticmethod
    def get_closing(obj):
        closing = obj.closing.strftime('%Y-%m-%d %H:%M:%S') if obj.closing else ''
        return closing

    @staticmethod
    def get_open(obj):
        open = obj.open.strftime('%Y-%m-%d %H:%M:%S') if obj.open else ''
        return open

    @staticmethod
    def get_next_open(obj):
        next_open = obj.next_open.strftime('%Y-%m-%d %H:%M:%S') if obj.next_open else ''
        return next_open

    @staticmethod
    def get_is_timeout(obj):
        now_time = datetime.now()
        if now_time >= obj.open and obj.special_code:
            return 1
        else:
            return 0

    @staticmethod
    def get_starting(obj):
        starting = obj.starting.strftime('%Y-%m-%d %H:%M:%S') if obj.starting else ''
        return starting
