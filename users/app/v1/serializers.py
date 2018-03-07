# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ...models import User, UserRecharge, DailyLog, DailySettings, UserMessage, Message



class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户退出登录
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    @staticmethod
    def validate_password(value):
        if len(value) < 6:
            raise serializers.ValidationError("password can't less than 6")
        return value

    @staticmethod
    def validate_username(value):
        user = User.objects.filter(username=value)
        if len(user) > 0:
            raise serializers.ValidationError("username exists")
        return value

    def save(self, **kwargs):
        user = super().save(**kwargs)
        if 'password' in self.validated_data:
            password = self.validated_data['password']
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        return super().to_representation(instance)

    class Meta:
        model = User
        fields = ("id", "username", "password", "avatar")


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息
    """
    telephone = serializers.SerializerMethodField()
    pass_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nickname", "avatar", "meth", "ggtc", "is_sound", "is_notify", "telephone", "pass_code")

    @staticmethod
    def get_telephone(obj):  # 我的选项
        if obj.telephone == '' or obj.telephone is None:
            return "未绑定"
        else:
            return obj.telephone

    @staticmethod
    def get_pass_code(obj):  # 我的选项
        if obj.pass_code == '' or obj.pass_code is None:
            if obj.telephone == '' or obj.telephone is None:
                return "请先绑定手机"
            else:
                return "未设置"
        else:
            return "已设置"



class ListSerialize(serializers.ModelSerializer):
    """
    用户列表
    """
    class Meta:
        model = User
        fields = ("id", "nickname")


class DailySerialize(serializers.ModelSerializer):
    """
    签到
    """
    class Meta:
        model = DailySettings
        fields = ("id", "days", "coin", "rewards")



class AssetsSerialize(serializers.ModelSerializer):
    """
    用户资产
    """
    class Meta:
        model = User
        fields = ()

    # @staticmethod
    # def get_eth(obj):
    #     # ETH




class RankingSerialize(serializers.ModelSerializer):
    """
    排行榜
    """
    class Meta:
        model = User
        fields = ("id", "avatar", "nickname")


class MessageSerialize(serializers.ModelSerializer):
    """
    通知列表
    """
    type = serializers.SerializerMethodField()         # 消息类型
    title = serializers.SerializerMethodField()       # 消息标题
    # public_sign = serializers.SerializerMethodField()     #  公共消息标记
    # system_sign = serializers.SerializerMethodField()     #  系统消息标记

    class Meta:
        model = UserMessage
        fields = ("id", "message", "type", "title", "status", "created_at")

    @staticmethod
    def get_type(obj):  # 消息类型
        list = Message.objects.get(pk=obj.message_id)
        type = list.type
        return type


    @staticmethod
    def get_title(obj):  # 消息标题
        list = Message.objects.get(pk=obj.message_id)
        title = list.title
        return title

