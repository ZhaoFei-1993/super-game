# -*- coding: UTF-8 -*-
import time
import pytz
from django.db.models import Q
from rest_framework import serializers
from ...models import User, DailySettings, UserMessage, Message, UserCoinLock, UserRecharge, CoinLock, UserPresentation
from quiz.models import Record, Quiz
from api import settings
from datetime import datetime


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
    is_passcode = serializers.SerializerMethodField()
    win_ratio = serializers.SerializerMethodField()
    quiz_push = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nickname", "avatar", "meth", "ggtc", "telephone", "is_passcode",
                  "eth_address", "win_ratio", "quiz_push")

    @staticmethod
    def get_telephone(obj):  # 电话号码
        if obj.telephone == '' or obj.telephone is None:
            return "未绑定"
        else:
            return obj.telephone

    @staticmethod
    def get_is_passcode(obj):  # 密保
        if obj.pass_code == '' or obj.pass_code is None:
            return "未设置"
        else:
            return "已设置"

    @staticmethod
    def get_win_ratio(obj):  # 胜率
        total_count = Record.objects.filter(~Q(earn_coin='0'), user_id=obj.id).count()
        win_count = Record.objects.filter(user_id=obj.id, earn_coin__gt=0).count()
        if total_count == 0 or win_count == 0:
            win_ratio = "0%"
        else:
            record_count = round(win_count / total_count * 100, 2)
            win_ratio = str(record_count) + "%"
        return win_ratio

    @staticmethod
    def get_quiz_push(obj):
        quiz = Quiz.objects.filter(Q(status=5) | Q(status=11), Q(is_delete=False)).order_by('-total_people')[:10]
        data = []
        for i in quiz:
            time = i.begin_at.strftime('%H:%M')
            name = i.host_team + "VS" + i.guest_team
            quiz_push = str(time) + " " + name
            data.append({
                'quiz_push': quiz_push,
            })
        return data


class DailySerialize(serializers.ModelSerializer):
    """
    签到
    """

    class Meta:
        model = DailySettings
        fields = ("id", "days", "rewards")


class MessageListSerialize(serializers.ModelSerializer):
    """
    通知列表
    """
    type = serializers.SerializerMethodField()  # 消息类型
    # type = serializers.SlugRelatedField(read_only=True, slug_field="type")
    # title = serializers.SlugRelatedField(read_only=True, slug_field="title")
    title = serializers.SerializerMethodField()  # 消息标题
    created_at = serializers.SerializerMethodField()

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

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data


class AssetSerialize(serializers.ModelSerializer):
    """
    资产信息
    """
    period = serializers.CharField(source='coin_lock.period')
    profit = serializers.DecimalField(source='coin_lock.profit', max_digits=100000, decimal_places=3)
    time_delta = serializers.SerializerMethodField()

    class Meta:
        model = UserCoinLock
        fields = ("id", "amount", "period", 'profit', 'created_at', 'end_time', 'time_delta')

    @staticmethod
    def get_time_delta(obj):
        now = datetime.utcnow()
        now = now.replace(tzinfo=pytz.timezone('UTC'))
        if now >= obj.end_time:
            return "已解锁"
        else:
            delta = obj.end_time - now
            d = delta.days
            h = int(delta.seconds / 3600)
            m = int((delta.seconds % 3600) / 60)
            s = int(delta.seconds % 60)
            value = '剩余锁定时间:%d天%d小时%d分%d秒' % (d, h, m, s)
            for item in {'0天': d, '0小时': h, '0分': m}.items():
                if item[0] in value and item[1] == 0:
                    value = value.replace(item[0], '')
            return value


class PresentationSerialize(serializers.ModelSerializer):
    """
    提现记录
    """

    class Meta:
        model = UserPresentation
        fields = ("id", "user", "amount", "rest", "created_at", "updated_at", "status")
