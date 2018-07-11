# -*- coding: UTF-8 -*-
from rest_framework import serializers
from django.utils import timezone
import time
from ..models import CoinLock, Coin, UserCoinLock, UserCoin, User, CoinDetail, LoginRecord, UserInvitation, \
    UserRecharge, \
    CoinOutServiceCharge, IntInvitation, UserPresentation, Message
from chat.models import Club
from quiz.models import Record
from datetime import datetime
from django.db import connection
from utils.functions import get_sql


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户表
    """
    source = serializers.SerializerMethodField()  # 来源
    # status = serializers.SerializerMethodField()     # 状态
    telephone = serializers.SerializerMethodField()  # 电话
    pass_code = serializers.SerializerMethodField()  # 密保
    degree = serializers.SerializerMethodField()  # 参与竞猜数
    created_at = serializers.SerializerMethodField()  # 创建时间
    assets = serializers.SerializerMethodField()  # 创建时间
    is_robot = serializers.SerializerMethodField()  # 是否为机器人

    class Meta:
        model = User
        fields = (
            "id", "username", "avatar", "nickname", "source", "integral", "telephone", "is_robot", "created_at",
            "status", "pass_code",
            "degree",
            "assets", "url")

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_source(obj):
        register_type = obj.REGISTER_TYPE[int(obj.register_type) - 1][1]
        source = obj.SOURCE_CHOICE[int(obj.source) - 1][1]
        data = str(register_type) + "-" + str(source)
        return data

    @staticmethod
    def get_is_robot(obj):
        if obj.is_robot == False:
            data = "0"
        elif obj.is_robot == True:
            data = "1"
        return data

    @staticmethod
    def get_pass_code(obj):
        if obj.pass_code == '' or obj.pass_code is None:
            return "未设置密保"
        else:
            return obj.telephone

    @staticmethod
    def get_telephone(obj):  # 电话号码
        if obj.telephone == '' or obj.telephone is None:
            return "未绑定电话"
        else:
            return obj.telephone

    @staticmethod
    def get_degree(obj):  # 参与竞猜数
        data = Record.objects.filter(user_id=obj.id).count()
        return data

    @staticmethod
    def get_assets(obj):  # 参与竞猜数
        list = UserCoin.objects.filter(user_id=obj.id)
        data = []
        for i in list:
            coin = Coin.objects.get(pk=i.coin_id)
            data.append({
                "coin": coin.name,
                "balance": i.balance
            })
        return data


class CoinLockSerializer(serializers.HyperlinkedModelSerializer):
    """
    货币锁定周期表序列化
    """
    coin_range = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    admin = serializers.SlugRelatedField(read_only=True, slug_field="username")
    Coin = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = CoinLock
        fields = ("id", "period", "profit", "coin_range", "Coin", "admin", "created_at", "url")

    @staticmethod
    def get_coin_range(obj):
        coin_range = str(obj.limit_start) + "-" + str(obj.limit_end)
        return coin_range

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data


class CurrencySerializer(serializers.HyperlinkedModelSerializer):
    """
    货币种类表序列化
    """
    created_at = serializers.SerializerMethodField()
    # is_lock = serializers.SerializerMethodField()
    admin = serializers.SlugRelatedField(read_only=True, slug_field="username")
    value = serializers.SerializerMethodField()

    class Meta:
        model = Coin
        fields = ("id", "icon", "name", "exchange_rate", "admin", "created_at", "cash_control", "betting_toplimit",
                  "betting_control", "coin_order", "url", "value", "coin_accuracy", "is_eth_erc20")

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_value(obj):
        try:
            values = CoinOutServiceCharge.objects.get(coin_out_id=obj.id)
        except Exception:
            return ''
        return values.value

    # @staticmethod
    # def get_is_lock(obj):  # 时间
    #     if obj.is_lock == False:
    #         data = "允许"
    #     if obj.is_lock == True:
    #         data = "不允许"
    #     return data


class UserCoinLockSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户锁定记录表
    """
    end_time = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    dividend = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field="nickname")
    coin_lock = serializers.SlugRelatedField(read_only=True, slug_field="period")

    class Meta:
        model = UserCoinLock
        fields = ("id", "user", "coin_lock", "amount", "end_time", "created_at", "dividend", "is_free")

    @staticmethod
    def get_end_time(obj):  # 结束时间
        data = obj.end_time.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_dividend(obj):  # 时间
        coinlock = CoinLock.objects.get(pk=obj.coin_lock_id)
        dividend = int(obj.amount) * float(coinlock.profit)
        return dividend

    @staticmethod
    def get_is_free(obj):
        is_free = obj.is_free
        data = "绑定中"
        if is_free == 1:
            data = "已解锁"
        return data


class UserCoinSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户资产
    """

    icon = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    coin = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field="nickname")

    class Meta:
        model = UserCoin
        fields = ("id", "coin", "user", "username", "icon", "address")

    @staticmethod
    def get_icon(obj):
        try:
            list = Coin.objects.get(pk=obj.coin_id)
        except Exception:
            return ''
        data = list.icon
        return data

    @staticmethod
    def get_coin(obj):
        try:
            coin = Coin.objects.get(pk=obj.coin_id)
        except Exception:
            return ''
        data = str(obj.balance) + " " + str(coin.name)
        return data

    @staticmethod
    def get_username(obj):
        try:
            list = User.objects.get(pk=obj.user_id)
        except Exception:
            return ''
        data = list.username
        return data


class CoinDetailSerializer(serializers.ModelSerializer):
    """
    用户资金明细
    """
    coin_name = serializers.CharField(source="coin.name")
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = CoinDetail
        fields = ("coin", "coin_name", "amount", "rest", "sources", "created_at")

    @staticmethod
    def get_created_at(obj):
        created_time = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return created_time


# class InviterInfoSerializer(serializers.ModelSerializer):
#     source = serializers.CharField(source='user.source')
#     telephone = serializers.CharField(source='user.telephone')
#     nickname = serializers.CharField(source='user.nickname')
#     login_time = serializers.SerializerMethodField()
#     created_at = serializers.SerializerMethodField()
#
#     class Meta:
#         model = LoginRecord
#         fields = ("id", "user", "login_time", "ip", "source", "telephone", "nickname", "created_at")
#
#     @staticmethod
#     def get_login_time(obj):
#         if obj.login_time != None or obj.login_time == '':
#             login_t = obj.login_time.strftime('%Y-%m-%d %H:%M')
#             return login_t
#         else:
#             return ''
#
#     @staticmethod
#     def get_created_at(obj):
#         created_at = obj.user.created_at.strftime('%Y-%m-%d %H:%M')
#         return created_at


class UserAllSerializer(serializers.ModelSerializer):
    """
    用户管理
    """
    created_at = serializers.SerializerMethodField()
    login_time = serializers.SerializerMethodField()
    login_address = serializers.SerializerMethodField()
    inviter = serializers.SerializerMethodField()
    inviter_id = serializers.SerializerMethodField()
    invite_new = serializers.SerializerMethodField()
    integral = serializers.SerializerMethodField()
    ip_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'telephone', 'nickname', 'created_at', 'login_time', 'ip_address', 'login_address', 'integral',
            'inviter', 'inviter_id', 'invite_new', 'status', 'is_block', 'ip_count')

    @staticmethod
    def get_created_at(obj):
        value = obj.created_at.strftime('%Y-%m-%d %H:%M')
        return value

    @staticmethod
    def get_login_time(obj):
        # login_time = LoginRecord.objects.select_related().filter(user_id=obj.id).order_by('-login_time').first()
        sql = "select ip, max(login_time) from users_loginrecord"
        sql += " where user_id=" + str(obj.id)
        sql += " group by ip"
        ip = get_sql(sql)
        if len(ip) > 0:
            return datetime.strftime(ip[0][1], '%Y-%m-%d %H:%M')
        else:
            return ''

    @staticmethod
    def get_login_address(obj):
        # ip_address = LoginRecord.objects.select_related().filter(user_id=obj.id).order_by('-login_time').first()
        sql = "select ip, max(login_time) from users_loginrecord"
        sql += " where user_id=" + str(obj.id)
        sql += " group by ip"
        ip = get_sql(sql)
        if len(ip) > 0:
            return ip[0][0]
        else:
            return ''

    @staticmethod
    def get_inviter(obj):

        sql = 'select nickname from users_user as a'
        sql += ' inner join users_userinvitation b on a.id=b.invitee_one'
        sql += ' where ' + str(obj.id) + '=b.inviter_id'
        dt_all = get_sql(sql)
        if len(dt_all) == 0:
            # inv = UserInvitation.objects.filter(invitee_one=obj.id).values('inviter_id')
            sql = 'select nickname from users_user as a'
            sql += ' inner join users_intinvitation b on a.id=b.invitee'
            sql += ' where ' + str(obj.id) + '=b.inviter_id'
            dt_all = get_sql(sql)
            if len(dt_all) == 0:
                return ''
        nickname = dt_all[0][0] if dt_all[0][0] else ''
        #     inv = IntInvitation.objects.filter(invitee=obj.id).values('inviter_id')
        #     if len(inv)==0:
        #         return ''
        # try:
        #     user = User.objects.get(id=inv[0][0])
        # except Exception:
        #     return ''
        return nickname

    @staticmethod
    def get_inviter_id(obj):
        cursor = connection.cursor()
        sql = "select inviter_id from users_userinvitation"
        sql += " where invitee_one=" + str(obj.id)
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
        if len(dt_all) == 0:
            sql = "select inviter_id from users_intinvitation"
            sql += " where invitee=" + str(obj.id)
            cursor.execute(sql, None)
            dt_all = cursor.fetchall()
            if len(dt_all) == 0:
                return ''
        inviter_id = dt_all[0][0] if dt_all[0][0] else ''
        return inviter_id
        # inv = UserInvitation.objects.filter(invitee_one=obj.id)
        # if not inv.exists():
        #     inv = IntInvitation.objects.filter(invitee=obj.id)
        #     if not inv.exists():
        #         return ''
        # return inv[0].inviter_id

    @staticmethod
    def get_invite_new(obj):
        # invitee_one = UserInvitation.objects.filter(inviter=obj).count()
        sql = 'select count(id) from users_userinvitation'
        sql += ' where inviter_id=' + str(obj.id)
        dt1 = get_sql(sql)
        if len(dt1) > 0:
            dt1_count = dt1[0][0]
        else:
            dt1_count = 0

        sql = 'select count(id) from users_intinvitation'
        sql += ' where inviter_id=' + str(obj.id)
        dt2 = get_sql(sql)
        if len(dt2) > 0:
            dt2_count = dt2[0][0]
        else:
            dt2_count = 0
        # invitee = IntInvitation.objects.filter(inviter=obj).count()
        return dt1_count + dt2_count

    @staticmethod
    def get_integral(obj):
        try:
            integral = UserCoin.objects.get(user_id = obj.id, coin_id=6)
        except Exception:
            return 0
        return round(float(integral.balance),2)

    @staticmethod
    def get_ip_count(obj):
        if obj.ip_address == '':
            return 0
        else:
            ip = obj.ip_address.rsplit('.', 1)[0]
            cursor = connection.cursor()
            sql = "select count(id) from users_user"
            sql += " where ip_address LIKE '%s." % ip + "%'"
            cursor.execute(sql, None)
            dt_all = cursor.fetchall()
            ip_count = dt_all[0][0] if dt_all[0][0] else 0
            # ip_count = User.objects.filter(ip_address__contains=ip).count()
            return ip_count





class CoinDetailSerializer(serializers.ModelSerializer):
    """
    明细记录
    """
    telephone = serializers.CharField(source='user.telephone')
    user_name = serializers.CharField(source='user.username')
    created_at = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = CoinDetail
        fields = ("user", "telephone", "user_name", "coin_name", "amount", "rest", "created_at", "sources")

    @staticmethod
    def get_created_at(obj):
        created_time = obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return created_time

    @staticmethod
    def get_sources(obj):
        choice = CoinDetail.TYPE_CHOICE
        for x in choice:
            if int(obj.sources) == x[0]:
                return x[1]


class CoinBackendDetailSerializer(serializers.ModelSerializer):
    """
    后台资产明细页面
    """
    username = serializers.CharField(source='user.username')
    coin_name = serializers.CharField(source='coin.name')
    room_id = serializers.SerializerMethodField()

    class Meta:
        model = UserCoin
        fields = ('username', 'coin_name', 'room_id', 'balance', 'coin', 'user')

    @staticmethod
    def get_room_id(obj):
        try:
            room = Club.objects.get(coin_id=obj.coin.id)
        except Exception:
            return ''
        return room.id


class UserRechargeSerializer(serializers.ModelSerializer):
    """
    用户充值序列
    """
    username = serializers.CharField(source='user.username')
    coin_name = serializers.CharField(source='coin.name')
    trade_at = serializers.SerializerMethodField()
    confirm_at = serializers.SerializerMethodField()

    class Meta:
        model = UserRecharge
        fields = (
            'username', 'user', 'coin', 'coin_name', 'amount', 'address', 'txid', 'confirmations', 'trade_at',
            'confirm_at')

    @staticmethod
    def get_trade_at(obj):
        trade_time = obj.trade_at.strftime('%Y-%m-%d %H:%M:%S')
        return trade_time

    @staticmethod
    def get_confirm_at(obj):
        confirm_time = obj.confirm_at.strftime('%Y-%m-%d %H:%M:%S')
        return confirm_time


class IPAddressSerializer(serializers.ModelSerializer):
    """
    同ip用户列表
    """

    login_times = serializers.SerializerMethodField()
    recharges = serializers.SerializerMethodField()
    presents = serializers.SerializerMethodField()
    present_success = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'ip_address', 'login_times', 'recharges', 'presents', 'present_success', 'is_block',
                  'created_at')

    @staticmethod
    def get_login_times(obj):
        login_times = LoginRecord.objects.filter(user_id=obj.id).count()
        return login_times

    @staticmethod
    def get_recharges(obj):
        recharges = UserRecharge.objects.filter(user_id=obj.id).count()
        return recharges

    @staticmethod
    def get_presents(obj):
        presents = UserPresentation.objects.filter(user_id=obj.id).count()
        return presents

    @staticmethod
    def get_present_success(obj):
        present_success = UserPresentation.objects.filter(user_id=obj.id, status=1).count()
        return present_success

    @staticmethod
    def get_created_at(obj):
        created_time = obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return created_time


class MessageBackendSerializer(serializers.ModelSerializer):
    """
    消息序列化
    """
    type = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('id', 'type', 'title', 'title_en', 'content', 'content_en', 'is_deleted', 'created_at')

    @staticmethod
    def get_type(obj):
        type = Message.TYPE_CHOICE[int(obj.type) - 1][1]
        return type

    @staticmethod
    def get_created_at(obj):
        created_time = obj.created_at.strftime('%Y-%m-%d %H:%M')
        return created_time
