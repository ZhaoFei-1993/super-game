# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ..models import Club

class ClubBackendSerializer(serializers.ModelSerializer):

    coin_name = serializers.CharField(source='coin.name')
    created_at = serializers.SerializerMethodField()
    is_recommend = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = ('id', 'room_title', 'autograph', 'icon', 'created_at', 'room_number', 'coin_name', 'is_recommend', 'is_dissolve')

    @staticmethod
    def get_created_at(obj):
        create_time = obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return create_time

    @staticmethod
    def get_is_recommend(obj):
        choice = Club.STATUS_CHOICE
        for x in choice:
            if int(obj.is_recommend) == x[0]:
                recommend = x[1]
                return recommend