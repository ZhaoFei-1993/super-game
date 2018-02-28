# -*- coding: UTF-8 -*-
from rest_framework import serializers
from .models import Admin, Role


class InfoSerialize(serializers.ModelSerializer):
    """
    管理信息
    """
    class Meta:
        model = Admin
        fields = ("id", "username", "truename")


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
