# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import User


class ListSerialize(serializers.ModelSerializer):
    """
    用户列表
    """
    class Meta:
        model = User
        fields = ("id", "nickname")


class InfoSerialize(serializers.ModelSerializer):
    """
    用户信息
    """
    class Meta:
        model = User
        fields = ("id", "nickname", "telephone")
