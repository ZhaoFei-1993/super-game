# -*- coding: UTF-8 -*-

import pytz
from django.db.models import Q
from rest_framework import serializers
from ...models import User, DailySettings, UserMessage, Message, UserCoinLock, UserRecharge, CoinLock, \
    UserPresentation, UserCoin, Coin, CoinValue, DailyLog, CoinDetail, IntegralPrize, CoinOutServiceCharge, \
    CoinGiveRecords, Countries
from quiz.models import Record, Quiz
from django.db import connection
from base.exceptions import ParamErrorException
from base import code as error_code
from utils.functions import amount, sign_confirmation, amount_presentation, normalize_fraction, get_sql
from api import settings
from datetime import timedelta, datetime
from django.utils import timezone
from django.core.cache import caches
from decimal import Decimal


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
    telephone = serializers.SerializerMethodField()  # 用户电话
    is_passcode = serializers.SerializerMethodField()
    win_ratio = serializers.SerializerMethodField()
    quiz_push = serializers.SerializerMethodField()
    is_user = serializers.SerializerMethodField()
    integral = serializers.SerializerMethodField()

    # usercoin = serializers.SerializerMethodField()
    # usercoin_avatar = serializers.SerializerMethodField()
    # ggtc_avatar = serializers.SerializerMethodField()
    # ggtc = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "nickname", "avatar", "integral", "telephone", "is_passcode",
            "win_ratio", "quiz_push", "is_sound", "is_notify", "is_user", "area_code")

    @staticmethod
    def get_telephone(obj):  # 电话号码
        if obj.telephone == '' or obj.telephone is None:
            return ""
        else:
            return obj.telephone

    @staticmethod
    def get_integral(obj):  # 电话号码
        integral = normalize_fraction(obj.integral, 2)
        return integral

    def get_is_user(self, obj):  # 电话号码
        user = self.context['request'].user.id
        if user == obj.id:
            is_user = 1
        else:
            is_user = 0
        return is_user

    @staticmethod
    def get_is_passcode(obj):  # 密保
        if obj.pass_code == '' or obj.pass_code is None:
            return 0
        else:
            return 1

    @staticmethod
    def get_usercoin(obj):  # 代币余额
        usercoin = UserCoin.objects.get(user_id=obj.id, is_opt=True)
        return usercoin.balance

    # @staticmethod
    # def get_ggtc(obj):  # GGTC余额
    #     ggtc = Coin.objects.get(type=1)
    #     userggtc = UserCoin.objects.get(user_id=obj.id, coin_id=ggtc.id)
    #     return userggtc.balance
    #
    # @staticmethod
    # def get_ggtc_avatar(obj):  # GSG图片
    #     ggtc = Coin.objects.get(type=1)
    #     return ggtc.icon

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
    rewards = serializers.SerializerMethodField()  # 消息类型
    icon = serializers.SerializerMethodField()  # 图片
    name = serializers.SerializerMethodField()  # 昵称

    class Meta:
        model = DailySettings
        fields = ("id", "days", "rewards", "icon", "name", "is_sign", "is_selected")

    @staticmethod
    def get_rewards(obj):  # 金额
        date_last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_date = "2018-06-24 00:00:00"
        if date_last > end_date:
            rewards = normalize_fraction(obj.rewards, 2)
        else:
            if obj.days == 1:
                rewards = 6
            if obj.days == 2:
                rewards = 8
            if obj.days == 3:
                rewards = 10
            if obj.days == 4:
                rewards = 12
            if obj.days == 5:
                rewards = 14
            if obj.days == 6:
                rewards = 16
            if obj.days == 7:
                rewards = 18
        return rewards

    @staticmethod
    def get_icon(obj):  # 图
        date_last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_date = "2018-06-24 00:00:00"
        if date_last >= end_date:
            icon = obj.coin.icon
        else:
            icon = ''
        return icon

    @staticmethod
    def get_name(obj):  # 昵称
        date_last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_date = "2018-06-24 00:00:00"
        if date_last >= end_date:
            name = obj.coin.name
        else:
            name = ''

        return name

    def get_is_sign(self, obj):  # 是否已签到
        user = self.context['request'].user.id
        sign = sign_confirmation(user)  # 判断是否签到
        yesterday = datetime.today() + timedelta(-1)
        yesterday_format = yesterday.strftime("%Y%m%d")
        yesterday_format = str(yesterday_format) + "000000"  # 今天凌晨00.00时间
        try:
            daily = DailyLog.objects.get(user_id=user)
            sign_date = daily.sign_date.strftime("%Y%m%d%H%M%S")  # 上次签到时间
        except DailyLog.DoesNotExist:
            daily = DailyLog()
            sign_date = str(0)

        is_sign = 0
        if sign_date < yesterday_format:  # 判断昨天签到没有
            is_sign = 0
            daily.number = 1
            daily.save()
        elif sign == 1 and daily.number == 0:
            is_sign = 1
        elif daily.number >= obj.days:
            is_sign = 1

        return is_sign

    def get_is_selected(self, obj):
        yesterday = datetime.today() + timedelta(-1)
        yesterday_format = yesterday.strftime("%Y%m%d")
        yesterday_format = str(yesterday_format) + "000000"
        user = self.context['request'].user.id
        sign = sign_confirmation(user)  # 判断是否签到
        try:
            daily = DailyLog.objects.get(user_id=user)
        except DailyLog.DoesNotExist:
            return 0
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
    titles = serializers.SerializerMethodField()  # 消息标题
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = UserMessage
        fields = ("id", "message", "type", "titles", "status", "created_at")

    @staticmethod
    def get_type(obj):  # 消息类型
        list = Message.objects.get(pk=obj.message_id)
        type = list.type
        return type

    def get_titles(self, obj):  # 消息标题
        list = Message.objects.get(pk=obj.message_id)
        type = list.type
        if int(type) == 3:
            title = obj.title
            if self.context['request'].GET.get('language') == 'en':
                title = obj.title_en
                if title == '' or title == None:
                    title = obj.title
        else:
            list = Message.objects.get(pk=obj.message_id)
            title = list.title
            if self.context['request'].GET.get('language') == 'en':
                title = list.title_en
                if title == '' or title == None:
                    title = list.title
        return title

    @staticmethod
    def get_created_at(obj):  # 时间
        created_time = obj.created_at
        # created_time = timezone.localtime(obj.created_at)
        data = created_time.strftime('%Y.%m.%d %H:%M')
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
            # s = int(delta.seconds % 60)
            value = '剩余锁定时间:%d天%d小时%d分' % (d, h, m)
            # for item in {'0天': d, '0小时': h, '0分': m}.items():
            #     if item[0] in value and item[1] == 0:
            #         value = value.replace(item[0], '')
            return value

    @staticmethod
    def get_created_at(obj):
        # created_time = timezone.localtime(obj.created_at)
        created_time = obj.created_at
        created_at = created_time.strftime("%Y/%m/%d")
        return created_at

    @staticmethod
    def get_end_time(obj):
        end_time = obj.end_time
        # end_time = timezone.localtime(obj.end_time)
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        return end_time


class PresentationSerialize(serializers.ModelSerializer):
    """
    提现记录
    """
    created_at = serializers.SerializerMethodField()
    coin_name = serializers.CharField(source="coin.name")
    user_name = serializers.CharField(source="user.username")
    telephone = serializers.CharField(source="user.telephone")
    is_block = serializers.BooleanField(source="user.is_block")
    ip_count = serializers.SerializerMethodField()
    recharge_times = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    rest = serializers.SerializerMethodField()

    class Meta:
        model = UserPresentation
        fields = (
            "id", "user_id", "user_name", "telephone", "coin_id", "coin_name", "amount", "address", "address_name",
            "rest",
            "created_at", "feedback", "status", "is_bill", "is_block", "ip_count", "recharge_times", "txid")

    @staticmethod
    def get_created_at(obj):
        # created_time = timezone.localtime(obj.created_at)
        created_time = obj.created_at
        created_at = created_time.strftime("%Y-%m-%d %H:%M:%S")
        return created_at

    # @staticmethod
    # def get_ip_count(obj):
    #     if obj.user.ip_address == '':
    #         return 0
    #     else:
    #         ip = obj.user.ip_address.rsplit('.', 1)[0]
    #         ip_count = User.objects.select_related().filter(ip_address__contains=ip).count()
    #         return ip_count
    @staticmethod
    def get_ip_count(obj):
        if obj.user.ip_address == '':
            return 0
        else:
            ip = obj.user.ip_address.rsplit('.', 1)[0]
            cursor = connection.cursor()
            sql = "select count(id) from users_user"
            sql += " where ip_address LIKE '%s." % ip + "%'"
            cursor.execute(sql, None)
            dt_all = cursor.fetchall()
            ip_count = dt_all[0][0] if dt_all[0][0] else 0
            # ip_count = User.objects.filter(ip_address__contains=ip).count()
            return ip_count

    @staticmethod
    def get_recharge_times(obj):
        # recharge_times = UserRecharge.objects.select_related().filter(user_id=obj.user_id).count()
        sql = "select count(id) from users_userrecharge where user_id = " + str(obj.user_id)
        dt_all = get_sql(sql)
        if len(dt_all) > 0:
            recharge_times = dt_all[0][0] if dt_all[0][0] else 0
        else:
            recharge_times = 0

        return recharge_times

    @staticmethod
    def get_amount(obj):
        return normalize_fraction(obj.amount, 8)

    @staticmethod
    def get_rest(obj):
        return normalize_fraction(obj.rest, 8)


class UserCoinSerialize(serializers.ModelSerializer):
    """
    用户余额
    """
    # name = serializers.SerializerMethodField()  # 代币名
    coin_name = serializers.SerializerMethodField()  # 交易所币名
    icon = serializers.SerializerMethodField()  # 代币头像
    balance = serializers.SerializerMethodField()
    exchange_rate = serializers.SerializerMethodField()  # 代币数
    coin_value = serializers.SerializerMethodField()  # 投注值
    locked_coin = serializers.SerializerMethodField()  # 审核中锁定的总币数
    recent_address = serializers.SerializerMethodField()
    min_present = serializers.SerializerMethodField()  # 提现限制最小金额
    service_charge = serializers.SerializerMethodField()  # 提现手续费
    service_coin = serializers.SerializerMethodField()  # 用于提现的币种
    coin_order = serializers.IntegerField(source='coin.coin_order')  # 币种顺序

    class Meta:
        model = UserCoin
        fields = ("id", "coin_name", "icon", "coin", "balance",
                  "exchange_rate", "address", "coin_value", "locked_coin", "service_charge", "service_coin",
                  "min_present", "coin_order", "recent_address")

    @staticmethod
    def get_balance(obj):
        balance = normalize_fraction(obj.balance, 8)
        if obj.coin.name == "USDT":
            coin_give = CoinGiveRecords.objects.get(user_id=obj.user_id, coin_give_id=1)
            lock_coin = normalize_fraction(coin_give.lock_coin, int(obj.coin.coin_accuracy))
            balance -= lock_coin
        return balance

    @staticmethod
    def get_coin_value(obj):
        data = []
        coin_value = CoinValue.objects.filter(coin_id=obj.coin.id).order_by('value')
        for i in coin_value:
            s = i.value
            data.append(
                {
                    'value': normalize_fraction(s, int(obj.coin.coin_accuracy))
                }
            )
        return data

    @staticmethod
    def get_coin_name(obj):  # 交易所币名
        try:
            list = Coin.objects.get(pk=obj.coin.id)
        except Exception:
            return ''
        # my_rule = list.TYPE_CHOICE[int(list.type) - 1][1]
        return list.name

    @staticmethod
    def get_icon(obj):  # 代币头像
        try:
            list = Coin.objects.get(pk=obj.coin.id)
        except Exception:
            return ''
        title = list.icon
        return title

    # @staticmethod
    # def get_total(obj):  # 总金额
    #     list = amount_presentation(obj.user.id, obj.coin.id)
    #     list = list + obj.balance
    #     list = [str(list), int(list)][int(list) == list]
    #     return list

    @staticmethod
    def get_min_present(obj):
        min_present = normalize_fraction(obj.coin.cash_control, int(obj.coin.coin_accuracy))
        return min_present

    @staticmethod
    def get_exchange_rate(obj):  # 币种交换汇率
        list = obj.coin.exchange_rate
        return list

    @staticmethod
    def get_locked_coin(obj):  # 提现申请期间锁定币数
        lock_coin = normalize_fraction(amount_presentation(obj.user.id, obj.coin.id), int(obj.coin.coin_accuracy))
        if obj.coin.name == "USDT":
            coin_give = CoinGiveRecords.objects.get(user_id=obj.user_id, coin_give_id=1)
            coin_lock_coin = normalize_fraction(coin_give.lock_coin, int(obj.coin.coin_accuracy))
            lock_coin += coin_lock_coin
        return lock_coin

    @staticmethod
    def get_recent_address(obj):  # 最近使用地址
        recent = UserPresentation.objects.filter(user_id=obj.user.id, coin_id=obj.coin.id).order_by('-created_at')[
                 :2].values('address', 'address_name')
        return list(recent)

    @staticmethod
    def get_service_charge(obj):
        try:
            coin_out = CoinOutServiceCharge.objects.get(coin_out=obj.coin)
        except Exception:
            return ''
        fee = normalize_fraction(coin_out.value, 4)
        return fee

    @staticmethod
    def get_service_coin(obj):
        try:
            coin_out = CoinOutServiceCharge.objects.get(coin_out=obj.coin)
        except Exception:
            return ''
        name = coin_out.coin_payment.name
        return name


class CoinOperateSerializer(serializers.ModelSerializer):
    """
    币中充值和提现操作记录
    """
    address = serializers.SerializerMethodField()
    address_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_code = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    service_charge = serializers.SerializerMethodField()

    class Meta:
        model = CoinDetail
        fields = (
            'id', 'amount', 'coin_name', 'icon', 'address', 'address_name', 'status', 'status_code', 'created_at',
            'month', 'time', 'service_charge')

    @staticmethod
    def get_amount(obj):
        try:
            icons = Coin.objects.get(name=obj.coin_name)
        except Exception:
            return ''
        amount = normalize_fraction(obj.amount, 6)
        return amount

    @staticmethod
    def get_service_charge(obj):
        try:
            icons = Coin.objects.get(name=obj.coin_name)
            coin_out = CoinOutServiceCharge.objects.get(coin_out=icons)
        except Exception:
            return ''
        coin_name = str(coin_out.coin_payment.name)
        coin_value = normalize_fraction(float(coin_out.value), int(coin_out.coin_payment.coin_accuracy))
        service_charge = "-" + str(coin_value) + str(coin_name)
        return service_charge

    @staticmethod
    def get_address(obj):
        if int(obj.sources) == 2:
            items = UserPresentation.objects.filter(user_id=obj.user.id, created_at__lte=obj.created_at,
                                                    coin__name=obj.coin_name).order_by('-created_at')
            if items.exists():
                item = items[0]
                return item.address
            else:
                return ''
        else:
            items = UserRecharge.objects.filter(user_id=obj.user.id, created_at__lte=obj.created_at,
                                                coin__name=obj.coin_name).order_by('-created_at')
            if items.exists():
                item = items[0]
                return item.address
            else:
                return ''

    # @staticmethod
    # def get_amount(obj):
    #     amount = round(float(obj.amount), 3)
    #     return amount

    @staticmethod
    def get_address_name(obj):
        if int(obj.sources) == 2:
            items = UserPresentation.objects.filter(user_id=obj.user.id, created_at__lte=obj.created_at,
                                                    coin__name=obj.coin_name).order_by('-created_at')
            if items.exists():
                item = items[0]
                return item.address_name
            else:
                return ''
        else:
            return ''

    @staticmethod
    def get_status(obj):
        if int(obj.sources) == 2:
            items = UserPresentation.objects.filter(user_id=obj.user.id, created_at__lte=obj.created_at,
                                                    coin__name=obj.coin_name).order_by('-created_at')
            if items.exists():
                item = items[0]
                status = item.TYPE_CHOICE[int(item.status)][1]
                return status
            else:
                return ''
        else:
            return '充值成功'

    @staticmethod
    def get_status_code(obj):
        if int(obj.sources) == 2:
            items = UserPresentation.objects.filter(user_id=obj.user.id, created_at__lte=obj.created_at,
                                                    coin__name=obj.coin_name).order_by('-created_at')
            if items.exists():
                item = items[0]
                status = item.TYPE_CHOICE[int(item.status)][0]
                return status
            else:
                return ''
        else:
            return ''

    @staticmethod
    def get_month(obj):
        month_time = obj.created_at
        # month_time = timezone.localtime(obj.created_at)
        month = month_time.strftime('%Y年%m月')
        return month

    @staticmethod
    def get_time(obj):
        # time_time = timezone.localtime(obj.created_at)
        time_time = obj.created_at
        time = time_time.strftime('%m-%d %H:%M')
        return time

    @staticmethod
    def get_created_at(obj):
        create_time = obj.created_at
        # create_time = timezone.localtime(obj.created_at)
        created_at = create_time.strftime('%Y-%m-%d %H:%M')
        return created_at

    @staticmethod
    def get_icon(obj):
        try:
            icons = Coin.objects.get(name=obj.coin_name)
        except Exception:
            return ''
        return icons.icon


class LuckDrawSerializer(serializers.ModelSerializer):
    """
    奖品列表序列化
    """
    prize_number = serializers.SerializerMethodField()
    prize_name = serializers.SerializerMethodField()

    class Meta:
        model = IntegralPrize
        fields = ('id', 'prize_name', 'icon', 'prize_number', 'prize_consume', 'prize_weight', 'created_at')

    def get_prize_name(self, obj):
        prize_name = obj.prize_name
        if self.context['request'].GET.get('language') == 'en' and prize_name == '谢谢参与':
            prize_name = 'Thanks'
        if self.context['request'].GET.get('language') == 'en' and prize_name == '再来一次':
            prize_name = 'Once again'
        return prize_name

    @staticmethod
    def get_prize_number(obj):
        prize_number = obj.prize_number
        if prize_number == 0:
            prize_number = ""
        else:
            if obj.prize_name == "GSG":
                prize_number = normalize_fraction(float(prize_number), 2)
            else:
                coin = Coin.objects.filter(name=obj.prize_name)
                prize_number = normalize_fraction(float(prize_number), int(coin[0].coin_accuracy))
        return prize_number


class CountriesSerialize(serializers.ModelSerializer):
    """
    电话区号序列化
    """

    class Meta:
        model = Countries
        fields = ('id', 'code', 'area_code', 'name_en', 'name_zh_CN', 'name_zh_HK', 'language')
