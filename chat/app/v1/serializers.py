# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import User
from base.validators import PhoneValidator


class MessageListSerialize(serializers.ModelSerializer):
    """
    序列号
    """
    type = serializers.SerializerMethodField()  # 消息类型

    class Meta:
        model = User
        fields = ("id", "type")

    @staticmethod
    def get_type(obj):  # 消息类型
        list = User.objects.get(pk=obj.message_id)
        type = list.type
        return type