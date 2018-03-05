# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import User


class ListSerialize(serializers.ModelSerializer):
    """
    用户列表
    """
    class Meta:
        model = User
        fields = ("id", "nickname")


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息
    """
    class Meta:
        model = User
        fields = ("id", "nickname", "avatar", "meth", "ggtc", )


class UserSerializer(serializers.ModelDurationField):
    """
    放着
    """

    pass