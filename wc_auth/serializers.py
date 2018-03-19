# -*- coding: UTF-8 -*-
from rest_framework import serializers
from .models import Admin, Role
from quiz.models import Quiz


class InfoSerialize(serializers.ModelSerializer):
    """
    管理信息
    """
    class Meta:
        model = Admin
        fields = ("id", "username", "truename")


class QuizSerialize(serializers.ModelSerializer):
    """
    竞猜表
    """
    key = serializers.SerializerMethodField()  # mapping to id

    class Meta:
        model = Quiz
        fields = ("key", "host_team", "guest_team", "begin_at", "match_name", "status")

    @staticmethod
    def get_key(obj):
        return obj.id


class RoleListSerialize(serializers.ModelSerializer):
    """
    管理员角色列表
    """
    key = serializers.SerializerMethodField()   # mapping to id

    class Meta:
        model = Role
        fields = ("key", "name")

    @staticmethod
    def get_key(obj):
        return obj.id
