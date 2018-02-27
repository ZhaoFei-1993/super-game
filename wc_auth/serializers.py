# -*- coding: UTF-8 -*-
from rest_framework import serializers
from .models import Admin


class InfoSerialize(serializers.ModelSerializer):
    """
    管理信息
    """
    class Meta:
        model = Admin
        fields = ("id", "username", "truename")
