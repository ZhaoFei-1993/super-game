# -*- coding: UTF-8 -*-

import pytz
from django.db.models import Q
from rest_framework import serializers
from ...models import User, DailySettings, UserMessage, Message, UserCoinLock, UserRecharge, CoinLock, \
    UserPresentation, UserCoin, Coin, CoinValue, DailyLog, CoinDetail
from quiz.models import Record, Quiz
from utils.functions import amount, sign_confirmation, amount_presentation
from api import settings
from datetime import timedelta, datetime
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
    # usercoin = serializers.SerializerMethodField()
    # usercoin_avatar = serializers.SerializerMethodField()
    ggtc_avatar = serializers.SerializerMethodField()
    ggtc = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
        "id", "nickname", "avatar", "ggtc_avatar", "ggtc", "telephone", "is_passcode",
        "win_ratio", "quiz_push", "is_sound", "is_notify")

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

    # @staticmethod
    # def get_ggtc_avatar(obj):  # GSG图片
    #     ggtc = Coin.objects.get(type=1)
    #     return ggtc.icon
    #
    # @staticmethod
    # def get_usercoin_avatar(obj):  # 代币图片
    #     usercoin = UserCoin.objects.get(user_id=obj.id, is_opt=True)
    #     coin = Coin.objects.get(pk=usercoin.coin_id)
    #     return coin.icon

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
    is_sign = serializers.SerializerMethodField()  # 消息类型
    is_selected = serializers.SerializerMethodField()  # 消息类型

    class Meta:
        model = DailySettings
        fields = ("id", "days", "rewards", "is_sign", "is_selected")

    def get_is_sign(self, obj):  # 消息类型
        user = self.context['request'].user.id
        sign = sign_confirmation(user)  # 判断是否签到
        daily = DailyLog.objects.get(user_id=user)
        is_sign = 0
        if sign == 1 and daily.number == 0:
            is_sign = 1
        else:
            if obj.days < daily.number or obj.days == daily.number:
                is_sign = 1
        return is_sign

    def get_is_selected(self, obj):
        yesterday = datetime.today() + timedelta(-1)
        yesterday_format = yesterday.strftime("%Y%m%d")
        yesterday_format = str(yesterday_format) + "000000"
        user = self.context['request'].user.id
        sign = sign_confirmation(user)  # 判断是否签到
        daily = DailyLog.objects.get(user_id=user)
        is_selected = 0
        sign_date = daily.sign_date.strftime("%Y%m%d%H%M%S")
        if sign_date < yesterday_format:  # 判断昨天签到没有
            is_selected = 0
            if obj.days == 1:
                is_selected = 1
        else:
            if sign == 1 and sign_date > yesterday_format:
                if obj.days == daily.number:
                    is_selected = 1
            elif sign == 0 and sign_date > yesterday_format:
                if obj.days == (daily.number + 1):
                    is_selected = 1
        return is_selected


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
        created_time = timezone.localtime(obj.created_at)
        data = created_time.strftime('%Y年%m月%d日%H:%M')
        return data


class AssetSerialize(serializers.ModelSerializer):
    """
    资产信息
    """
    period = serializers.CharField(source='coin_lock.period')
    profit = serializers.DecimalField(source='coin_lock.profit', max_digits=1000000, decimal_places=3)
    time_delta = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = UserCoinLock
        fields = ("id", "amount", "period", 'profit', 'created_at', 'end_time', 'time_delta', 'is_free')

    @staticmethod
    def get_time_delta(obj):
        now = datetime.utcnow()
        now = now.replace(tzinfo=pytz.timezone('UTC'))
        if obj.is_free:
            return "已解锁"
        else:
            delta = obj.end_time - now
            d = delta.days
            h = int(delta.seconds / 3600)
            m = int((delta.seconds % 3600) / 60)
            s = int(delta.seconds % 60)
            value = '剩余锁定时间:%d天%d小时%d分' % (d, h, m)
            # for item in {'0天': d, '0小时': h, '0分': m}.items():
            #     if item[0] in value and item[1] == 0:
            #         value = value.replace(item[0], '')
            return value

    @staticmethod
    def get_created_at(obj):
        created_time = timezone.localtime(obj.created_at)
        created_at = created_time.strftime("%Y-%m-%d %H:%M:%S")
        return created_at

    @staticmethod
    def get_end_time(obj):
        end_time = timezone.localtime(obj.end_time)
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        return end_time


class PresentationSerialize(serializers.ModelSerializer):
    """
    提现记录
    """
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = UserPresentation
        fields = ("id", "user", "coin", "amount","address","address_name","rest", "created_at", "updated_at", "status")

    @staticmethod
    def get_created_at(obj):
        created_time = timezone.localtime(obj.created_at)
        created_at = created_time.strftime("%Y-%m-%d %H:%M:%S")
        return created_at


class UserCoinSerialize(serializers.ModelSerializer):
    """
    用户余额
    """
    name = serializers.SerializerMethodField()  # 代币名
    coin_name = serializers.SerializerMethodField()  # 交易所币名
    icon = serializers.SerializerMethodField()  # 代币头像
    total = serializers.SerializerMethodField()  # 总金额
    exchange_rate = serializers.SerializerMethodField()  # 代币数
    coin_value = serializers.SerializerMethodField()  # 投注值
    locked_coin = serializers.SerializerMethodField() #审核中锁定的总币数
    # service_charge = serializers.CharField(source='coin.service_charge')
    recent_address = serializers.SerializerMethodField()

    class Meta:
        model = UserCoin
        fields = ("id", "name", "coin_name", "icon", "coin", "total", "balance",
                  "exchange_rate", "address", "coin_value", "locked_coin", "recent_address")

    @staticmethod
    def get_name(obj):  # 代币名
        list = Coin.objects.get(pk=obj.coin_id)
        title = list.name
        return title

    @staticmethod
    def get_coin_value(obj):
        coin_id = obj.coin_id
        data = []
        coin_value = CoinValue.objects.filter(coin_id=coin_id).order_by('value')
        for i in coin_value:
            s = i.value
            data.append(
                {
                    'value': [str(s), int(s)][int(s) == s]
                }
            )
        return data

    @staticmethod
    def get_coin_name(obj):  # 交易所币名
        list = Coin.objects.get(pk=obj.coin_id)
        my_rule = ''
        if int(list.type) != 1:
            my_rule = list.TYPE_CHOICE[int(list.type) - 1][1]
        return my_rule

    @staticmethod
    def get_icon(obj):  # 代币头像
        list = Coin.objects.get(pk=obj.coin_id)
        title = list.icon
        return title


    @staticmethod
    def get_total(obj):  # 总金额
        list = amount_presentation(obj.user.id, obj.coin.id)
        list = list + obj.balance
        list = [str(list), int(list)][int(list) == list]
        return list



    @staticmethod
    def get_exchange_rate(obj):  # 币种交换汇率
        list = obj.coin.exchange_rate
        return list

    @staticmethod
    def get_locked_coin(obj): #提现申请期间锁定币数
        return amount_presentation(obj.user.id, obj.coin.id)


    @staticmethod
    def get_recent_address(obj): # 最近使用地址
        recent = UserPresentation.objects.filter(user_id=obj.user.id, coin_id=obj.coin.id).order_by('-created_at')[:2]
        temp_recent=[]
        for x in recent:
            temp_recent.append({x.address_name:x.address})
        return temp_recent


class CoinOperateSerializer(serializers.ModelSerializer):
    """
    币中充值和提现操作记录
    """
    address = serializers.SerializerMethodField()
    address_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = CoinDetail
        fields = ('id', 'amount', 'address', 'address_name', 'status', 'created_at', 'month', 'time')

    @staticmethod
    def get_address(obj):
        if int(obj.sources) == 2:
            item = UserPresentation.objects.get(user_id=obj.user.id, created_at=obj.created_at)
            return item.address
        else:
            item = UserRecharge.objects.get(user_id=obj.user.id, created_at=obj.created_at)
            return item.address

    @staticmethod
    def get_address_name(obj):
        if int(obj.sources) == 2:
            item = UserPresentation.objects.get(user_id=obj.user.id, created_at=obj.created_at)
            return item.address_name
        else:
            return None

    @staticmethod
    def get_status(obj):
        if int(obj.sources) == 2:
            item = UserPresentation.objects.get(user_id=obj.user.id, created_at=obj.created_at)
            status = item.TYPE_CHOICE[int(item.status)][1]
            return  status
        else:
            return '充值成功'

    @staticmethod
    def get_month(obj):
        month_time = timezone.localtime(obj.created_at)
        month = month_time.strftime('%Y年%m月')
        return month

    @staticmethod
    def get_time(obj):
        time_time = timezone.localtime(obj.created_at)
        time = time_time.strftime('%m-%d %H:%M')
        return time

    @staticmethod
    def get_created_at(obj):
        create_time = timezone.localtime(obj.created_at)
        created_at = create_time.strftime('%Y-%m-%d %H:%M')
        return created_at
