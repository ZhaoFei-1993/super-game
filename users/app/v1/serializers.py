# -*- coding: UTF-8 -*-

import pytz
from django.db.models import Q
from rest_framework import serializers
from ...models import User, DailySettings, UserMessage, Message, UserCoinLock, UserRecharge, CoinLock, \
    UserPresentation, UserCoin, Coin
from quiz.models import Record, Quiz
from utils.functions import amount
from api import settings
from datetime import datetime
from django.utils import timezone


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
    usercoin = serializers.SerializerMethodField()
    usercoin_avatar = serializers.SerializerMethodField()
    ggtc = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nickname", "avatar", "usercoin", "usercoin_avatar", "ggtc", "telephone", "is_passcode",
                  "eth_address", "win_ratio", "quiz_push", "is_sound", "is_notify")

    @staticmethod
    def get_telephone(obj):  # 电话号码
        if obj.telephone == '' or obj.telephone is None:
            return ""
        else:
            return obj.telephone

    @staticmethod
    def get_is_passcode(obj):  # 密保
        if obj.pass_code == '' or obj.pass_code is None:
            return "0"
        else:
            return "1"

    @staticmethod
    def get_usercoin(obj):  # 代币余额
        usercoin = UserCoin.objects.get(user_id=obj.id, is_opt=True)
        return usercoin.balance

    @staticmethod
    def get_ggtc(obj):  # GGTC余额
        ggtc = Coin.objects.get(type=1)
        userggtc = UserCoin.objects.get(user_id=obj.id, coin_id=ggtc.id)
        return userggtc.balance

    @staticmethod
    def get_usercoin_avatar(obj):  # 代币图片
        usercoin = UserCoin.objects.get(user_id=obj.id, is_opt=True)
        coin = Coin.objects.get(pk=usercoin.coin_id)
        return coin.icon

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
    created_at = serializers.SerializerMethodField()

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

    @staticmethod
    def get_created_at(obj):
        created_time = timezone.localtime(obj.created_at)
        created_at = created_time.strftime("%Y-%m-%d %H:%M:%S")
        return created_at



class PresentationSerialize(serializers.ModelSerializer):
    """
    提现记录
    """
    coin= serializers.CharField(source='coin.name')
    class Meta:
        model = UserPresentation
        fields = ("id", "user","coin","amount", "rest", "created_at", "updated_at", "status")


class UserCoinSerialize(serializers.ModelSerializer):
    """
    用户余额
    """
    name = serializers.SerializerMethodField()  # 代币名
    coin_name = serializers.SerializerMethodField()  # 交易所币名
    icon = serializers.SerializerMethodField()  # 代币头像
    lock_ggtc = serializers.SerializerMethodField()  # 代币锁定金额
    total = serializers.SerializerMethodField()  # 总金额
    coin = serializers.SerializerMethodField()  # 交易所币数
    aglie = serializers.SerializerMethodField()  # 代币数

    class Meta:
        model = UserCoin
        fields = ("id", "name", "coin_name", "icon", "lock_ggtc", "total", "coin", "aglie", "balance")

    @staticmethod
    def get_name(obj):  # 代币名
        list = Coin.objects.get(pk=obj.coin_id)
        title = list.name
        return title

    @staticmethod
    def get_coin_name(obj):  # 交易所币名
        list = Coin.objects.get(pk=obj.coin_id)
        my_rule = ''
        if int(list.type) != 1:
            my_rule = list.TYPE_CHOICE[int(list.type) - 1][0]
        return my_rule

    @staticmethod
    def get_icon(obj):  # 代币头像
        list = Coin.objects.get(pk=obj.coin_id)
        title = list.icon
        return title

    @staticmethod
    def get_lock_ggtc(obj):  # 代币锁定金额
        ggtc = Coin.objects.get(pk=obj.coin_id)
        list = 0
        if int(ggtc.type) == 1:
            list = amount(obj.user_id)
        return list

    @staticmethod
    def get_total(obj):  # 总金额
        ggtc = Coin.objects.get(pk=obj.coin_id)
        list = obj.balance
        if int(ggtc.type) == 1:
            coin = amount(obj.user_id)
            list = list + coin
        return list

    @staticmethod
    def get_coin(obj):  # 交易所币数
        coin = Coin.objects.get(pk=obj.coin_id)
        list = 0
        if int(coin.type) != 1:
            list = round(obj.balance / coin.exchange_rate, 4)
        return list

    @staticmethod
    def get_aglie(obj):  # 代币数
        coin = Coin.objects.get(pk=obj.coin_id)
        list = 0
        if int(coin.type) == 1:
            list = obj.balance
        return list

