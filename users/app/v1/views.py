# -*- coding: UTF-8 -*-
from django.db.models import Q
from .serializers import UserInfoSerializer, UserSerializer, \
    DailySerialize, MessageListSerialize, PresentationSerialize, AssetSerialize, UserCoinSerialize, \
    CoinOperateSerializer, LuckDrawSerializer
import qrcode
from ast import literal_eval
from quiz.app.v1.serializers import QuizSerialize
from ...models import User, DailyLog, DailySettings, UserMessage, Message
from django.core.cache import caches
from quiz.models import Quiz
from ...models import User, DailyLog, DailySettings, UserMessage, Message, \
    UserPresentation, UserCoin, Coin, UserRecharge, CoinDetail, \
    UserSettingOthors, UserInvitation, IntegralPrize, IntegralPrizeRecord
from chat.models import Club
from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView
from base.function import LoginRequired
from base.function import randomnickname, weight_choice
from sms.models import Sms
from datetime import timedelta, datetime
import time
import pytz
from decimal import Decimal
from django.conf import settings
from base import code as error_code
from base.exceptions import ParamErrorException, UserLoginException
from utils.functions import random_salt, sign_confirmation, message_hints, \
    message_sign, amount, value_judge, resize_img
from rest_framework_jwt.settings import api_settings
from django.db import transaction
import re
import os
from config.models import AndroidVersion
from config.serializers import AndroidSerializer
from utils.forms import ImageForm
from utils.models import Image as Im
from api.settings import MEDIA_DOMAIN_HOST, BASE_DIR
from django.db.models import Sum
from PIL import Image


class UserRegister(object):
    """
    用户公共处理类
    """
    cache = caches['memcached']

    def set_user_cache(self, key, value):
        self.cache.set(key, value)

    def get_user_cache(self, key):
        return self.cache.get(key)

    def delete_user_cache(self, key):
        return self.cache.delete(key)

    @staticmethod
    def get_register_type(username):
        """
        判断注册类型并返回
        :param username:
        :return:
        """
        if len(username) == 32:
            register_type = User.REGISTER_QQ
        if len(username) == 11:
            register_type = User.REGISTER_TELEPHONE
        else:
            register_type = User.REGISTER_WECHAT
        return register_type

    def get_access_token(self, source, user):
        """
        获取access_token
        :param source:
        :param user:
        :return:
        """
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # # 以用户名+用户来源（iOS、Android）为key，保存到缓存中
        # cache_key = user.username + source
        # self.set_user_cache(cache_key, token)

        return token

    def login(self, source, username, password):
        """
        用户登录
        :param source:   用户来源
        :param username: 用户账号
        :param password: 登录密码，第三方登录不提供
        :return:
        """
        token = None
        if password is None:
            try:
                user = User.objects.get(username=username)
            except Exception:
                raise UserLoginException(error_code=error_code.API_20103_TELEPHONE_UNREGISTER)
            token = self.get_access_token(source=source, user=user)
        else:
            try:
                user = User.objects.get(username=username)
            except Exception:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if user.check_password(password):
                token = self.get_access_token(source=source, user=user)
            else:
                raise UserLoginException(error_code=error_code.API_20104_LOGIN_ERROR)
            message = Message.objects.filter(type=1, created_at__gte=user.created_at)
            for i in message:
                message_id = i.id
                user_message = UserMessage.objects.filter(message=message_id, user=user.id)
                if len(user_message) == 0:
                    usermessage = UserMessage()
                    usermessage.user = user
                    usermessage.message = i
                    usermessage.save()

            #  生成货币余额表
            coin = Coin.objects.all()
            for i in coin:
                userbalance = UserCoin.objects.filter(coin_id=i.pk, user_id=user.id).count()
                if userbalance == 0:
                    usercoin = UserCoin()
                    usercoin.user_id = user.id
                    usercoin.coin_id = i.id
                    usercoin.is_opt = False
                    usercoin.save()
            #   邀请送HAND币
            user_invitation_number = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter=user.id,
                                                                   is_effective=1).count()
            if user_invitation_number > 0:
                user_invitation_info = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter=user.id,
                                                                     is_effective=1)
                try:
                    userbalance = UserCoin.objects.get(coin__name='HAND', user_id=user.id)
                except Exception:
                    return 0
                for a in user_invitation_info:
                    coin_detail = CoinDetail()
                    coin_detail.user = user
                    coin_detail.coin_name = 'HAND'
                    coin_detail.amount = '+' + str(a.money)
                    coin_detail.rest = userbalance.balance
                    coin_detail.sources = 4
                    coin_detail.save()
                    a.is_deleted = 1
                    a.save()
                    userbalance.balance += a.money
                    userbalance.save()

            # 注册送HAND币
            if user.is_money == 0:
                user_money = 2000
                try:
                    user_balance = UserCoin.objects.get(coin__name='HAND', user_id=user.id)
                except Exception:
                    return 0
                coin_detail = CoinDetail()
                coin_detail.user = user
                coin_detail.coin_name = 'HAND'
                coin_detail.amount = '+' + str(user_money)
                coin_detail.rest = user_balance.balance
                coin_detail.sources = 4
                coin_detail.save()
                user_balance.balance += user_money
                user_balance.save()
                user.is_money = 1
                user.save()
        return token

    @transaction.atomic()
    def register(self, source, username, password, avatar='', nickname='', ):
        """
        用户注册
        :param source:      用户来源：ios、android
        :param username:    用户账号：openid
        :param password     登录密码
        :param avatar:      用户头像，第三方登录提供
        :param nickname:    用户昵称，第三方登录提供
        :return:
        """
        # 根据username的长度判断注册type
        # 11 telephone
        # 32 QQ
        # 28 微信
        register_type = self.get_register_type(username)
        user = User()
        if len(username) == 11:
            user.telephone = username

        user.username = username
        user.source = user.__getattribute__(source.upper())
        user.set_password(password)
        user.register_type = register_type
        user.avatar = avatar
        user.nickname = nickname
        user.save()
        # 生成签到记录
        try:
            userinfo = User.objects.get(username=username)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        daily = DailyLog()
        daily.user_id = userinfo.id
        daily.number = 0
        yesterday = datetime.today() + timedelta(-1)
        daily.sign_date = yesterday.strftime("%Y-%m-%d %H:%M:%S")
        daily.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        daily.save()
        # 生成代币余额
        coin = Coin.objects.all()
        for i in coin:
            usercoin = UserCoin()
            usercoin.user_id = userinfo.id
            usercoin.coin_id = i.id
            # gsg = Coin.TYPE_CHOICE[0][1]
            # is_coin = Coin.TYPE_CHOICE[1][1]
            # if i.name == is_coin:
            #     usercoin.is_opt = True
            #     usercoin.address = 1008611
            # if i.name == gsg:
            #     usercoin.is_bet =True
            #     usercoin.address = 0
            usercoin.address = 10086
            usercoin.save()

        # 生成客户端加密串
        token = self.get_access_token(source=source, user=user)

        return token


class LoginView(CreateAPIView):
    """
    用户登录:
    用户已经注册-----》登录
    新用户---------》注册----》登录
    """

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')
        ur = UserRegister()
        value = value_judge(request, "username", "type")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        username = request.data.get('username')
        register_type = ur.get_register_type(username)

        avatar = settings.MEDIA_DOMAIN_HOST + "/images/avatar.png"
        if 'avatar' in request.data:
            avatar = request.data.get('avatar')
        type = request.data.get('type')  # 1 注册          2 登录
        regex = re.compile(r'^(1|2)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        user = User.objects.filter(username=username)
        if len(user) == 0:
            if int(type) == 2:
                raise ParamErrorException(error_code.API_10105_NO_REGISTER)

            if int(register_type) == 1 or int(register_type) == 2:
                password = random_salt(8)
                nickname = request.data.get('nickname')
                token = ur.register(source=source, nickname=nickname, username=username, avatar=avatar,
                                    password=password)

            else:
                code = request.data.get('code')
                message = Sms.objects.filter(telephone=username, code=code, type=Sms.REGISTER)
                if len(message) == 0:
                    return self.response({
                        'code': error_code.API_20402_INVALID_SMS_CODE
                    })
                nickname = randomnickname()
                password = request.data.get('password')
                print('password = ', password)
                token = ur.register(source=source, nickname=nickname, username=username, avatar=avatar,
                                    password=password)
        else:
            if int(type) == 1:
                raise ParamErrorException(error_code.API_10106_TELEPHONE_REGISTER)
            if int(register_type) == 1 or int(register_type) == 2:
                password = None
                token = ur.login(source=source, username=username, password=password)
            elif int(register_type) == 3:
                password = ''
                if 'password' in request.data:
                    password = request.data.get('password')
                token = ur.login(source=source, username=username, password=password)
            else:
                password = request.data.get('password')
                token = ur.login(source=source, username=username, password=password)
        return self.response({
            'code': 0,
            'data': {'access_token': token}})


class LogoutView(ListCreateAPIView):
    """
    用户退出登录
    """
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')

        ur = UserRegister()
        ur.delete_user_cache(request.user.username + source)

        return self.response({'code': 0})


class InfoView(ListAPIView):
    """
    用户信息
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        user = request.user
        roomquiz_id = kwargs['roomquiz_id']
        # roomquiz_id = request.GET.get('roomquiz_id')
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user_id = self.request.user.id
        is_sign = sign_confirmation(user_id)  # 是否签到
        is_message = message_hints(user_id)  # 是否有未读消息
        # ggtc_locked = amount(user_id)  # 该用户锁定的金额
        clubinfo = Club.objects.get(pk=roomquiz_id)
        coin_name = clubinfo.coin.name
        coin_id = clubinfo.coin.pk
        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        user_coin = usercoin.balance
        usercoin_avatar = clubinfo.coin.icon
        recharge_address = usercoin.address

        return self.response({'code': 0, 'data': {
            'user_id': items[0]["id"],
            'nickname': items[0]["nickname"],
            'avatar': items[0]["avatar"],
            'usercoin': [str(user_coin), int(user_coin)][int(user_coin) == user_coin],
            'coin_name': coin_name,
            'usercoin_avatar': usercoin_avatar,
            'recharge_address': recharge_address,
            'integral': items[0]["integral"],
            # 'ggtc_avatar': items[0]["ggtc_avatar"],
            'telephone': items[0]["telephone"],
            'is_passcode': items[0]["is_passcode"],
            # 'ggtc_locked': ggtc_locked,
            'is_message': is_message,
            'is_sound': items[0]["is_sound"],
            'is_notify': items[0]["is_notify"],
            'is_sign': is_sign}})


class QuizPushView(ListAPIView):
    """
    首页推送
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        quiz = Quiz.objects.filter(Q(status=5) | Q(status=11), Q(is_delete=False)).order_by('-total_people')[:10]
        data = []
        for i in quiz:
            time = i.begin_at.strftime('%H:%M')
            name = i.host_team + "VS" + i.guest_team
            quiz_push = str(time) + " " + name
            data.append({
                'quiz_push': quiz_push,
            })
        content = {'code': 0, 'data': data}
        return self.response(content)


class NicknameView(ListAPIView):
    """
    修改用户昵称
    """

    def put(self, request, *args, **kwargs):
        user = request.user
        if "avatar" in request.data:
            user.avatar = request.data.get("avatar")
        if "nickname" in request.data:
            user.nickname = request.data.get("nickname")
        user.save()

        content = {'code': 0, "data": request.data.get("nickname")}
        return self.response(content)


class BindTelephoneView(ListCreateAPIView):
    """
    绑定手机
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "telephone", "code")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        telephone = request.data.get('telephone')
        if "code" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20401_TELEPHONE_ERROR)

        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(telephone=telephone).order_by('-id').first()
        if (sms is None) or (sms.code != request.data.get('code')):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})

        if int(sms.type) != 1:
            return self.response({'code': error_code.API_40106_SMS_PARAMETER})
        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.now().timetuple())
        if current_time - time.mktime(sent_time.timetuple()) >= settings.SMS_CODE_EXPIRE_TIME:
            return self.response({'code': error_code.API_20403_SMS_CODE_EXPIRE})

        try:
            user = User.objects.get(id=self.request.user.id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user.telephone = telephone
        user.save()
        content = {'code': 0}
        return self.response(content)


class UnbindTelephoneView(ListCreateAPIView):
    """
    解除手机绑定
    """

    def post(self, request, *args, **kwargs):
        user_id = self.request.user.id
        try:
            userinfo = User.objects.get(pk=user_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(telephone=userinfo.telephone).order_by('-id').first()
        if (sms is None) or (sms.code != request.data.get('code')):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})

        if int(sms.type) != 2:
            return self.response({'code': error_code.API_40106_SMS_PARAMETER})
        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.now().timetuple())
        if current_time - time.mktime(sent_time.timetuple()) >= settings.SMS_CODE_EXPIRE_TIME:
            return self.response({'code': error_code.API_20403_SMS_CODE_EXPIRE})

        userinfo.telephone = ""
        userinfo.save()
        content = {'code': 0}
        return self.response(content)


class RankingView(ListAPIView):
    """
    排行榜
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.all().order_by('-integral', 'id')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        user = request.user
        user_arr = User.objects.all().values_list('id').order_by('-integral', 'id')[:100]
        my_ran = "未上榜"
        index = 0
        for i in user_arr:
            index = index + 1
            if i[0] == user.id:
                my_ran = index
        avatar = user.avatar
        nickname = user.nickname
        # win_ratio = user.victory
        # if user.victory == 0:
        #     win_ratio = 0
        # usercoin = UserCoin.objects.get(user_id=user.id, coin_id=1)
        my_ranking = {
            "user_id": user.id,
            "avatar": avatar,
            "nickname": nickname,
            "win_ratio": user.integral,
            "ranking": my_ran
        }
        list = []
        if 'page' not in request.GET:
            page = 1
        else:
            page = int(request.GET.get('page'))
        i = (page - 1) * 10
        for fav in Progress:
            i = i + 1
            user_id = fav.get('id')
            list.append({
                'user_id': user_id,
                'avatar': fav.get('avatar'),
                'nickname': fav.get('nickname'),
                'is_user': fav.get('is_user'),
                'win_ratio': int(fav.get('integral')),
                'ranking': i,
            })
            list.sort(key=lambda x: x["ranking"])

        return self.response({'code': 0, 'data': {'my_ranking': my_ranking, 'list': list, }})


class PasscodeView(ListCreateAPIView):
    """
    密保设置
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "passcode")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        passcode = request.data.get('passcode')
        if len(passcode) < 6:
            raise ParamErrorException(error_code=error_code.API_20602_PASS_CODE_LEN_ERROR)
        if "passcode" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20601_PASS_CODE_ERROR)
        try:
            user = User.objects.get(id=self.request.user.id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user.pass_code = passcode
        user.save()
        content = {'code': 0}
        return self.response(content)


class ForgetPasscodeView(ListCreateAPIView):
    """
    原密保校验
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "passcode")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        passcode = request.data.get('passcode')
        if "passcode" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20701_USED_PASS_CODE_)
        try:
            user = User.objects.get(id=self.request.user.id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if passcode != user.pass_code:
            raise ParamErrorException(error_code=error_code.API_20702_USED_PASS_CODE_ERROR)
        content = {'code': 0}
        return self.response(content)


class BackPasscodeView(ListCreateAPIView):
    """
     忘记密保
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "passcode", "code")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        passcode = request.data.get('passcode')
        user_id = self.request.user.id
        try:
            userinfo = User.objects.get(pk=user_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(telephone=userinfo.telephone).order_by('-id').first()
        if (sms is None) or (sms.code != request.data.get('code')):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})

        if int(sms.type) != 3:
            return self.response({'code': error_code.API_40106_SMS_PARAMETER})

        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.now().timetuple())
        if current_time - time.mktime(sent_time.timetuple()) >= settings.SMS_CODE_EXPIRE_TIME:
            return self.response({'code': error_code.API_20403_SMS_CODE_EXPIRE})

        if len(passcode) < 6:
            raise ParamErrorException(error_code=error_code.API_20802_PASS_CODE_LEN_ERROR)
        if "passcode" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20801_PASS_CODE_ERROR)

        userinfo.pass_code = passcode
        userinfo.save()
        content = {'code': 0}
        return self.response(content)


class SwitchView(ListCreateAPIView):
    """
    音效/消息免推送 开关
    """

    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "event", "status")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        event = request.data.get('event')
        status = request.data.get('status')
        if "event" not in request.data:
            raise ParamErrorException(error_code=error_code.API_10104_PARAMETER_EXPIRED)
        if "status" not in request.data:
            raise ParamErrorException(error_code=error_code.API_10104_PARAMETER_EXPIRED)

        regex = re.compile(r'^(0|1)$')
        if event is None or not regex.match(event):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if status is None or not regex.match(status):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        try:
            user = User.objects.get(id=self.request.user.id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(event) == 0:
            user.is_sound = status
        else:
            user.is_notify = status
        user.save()
        content = {'code': 0}
        return self.response(content)


class DailyListView(ListAPIView):
    """
    签到列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = DailySerialize

    def get_queryset(self):
        daily = DailySettings.objects.all().order_by('days')
        return daily

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append({
                "id": list["id"],
                "days": list["days"],
                "rewards": list["rewards"],
                "is_sign": list["is_sign"],
                "is_selected": list["is_selected"]
            })

        return self.response({'code': 0, 'data': data})


class DailySignListView(ListCreateAPIView):
    """
    点击签到
    """
    permission_classes = (LoginRequired,)

    def post(self, request):
        user_id = self.request.user.id
        sign = sign_confirmation(user_id)  # 判断是否签到
        yesterday = datetime.today() + timedelta(-1)
        yesterday_format = yesterday.strftime("%Y%m%d")
        yesterday_format = str(yesterday_format) + "000000"
        if sign == 1:
            raise ParamErrorException(error_code.API_30201_ALREADY_SING)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        try:
            daily = DailyLog.objects.get(user_id=user_id)
            sign_date = daily.sign_date.strftime("%Y%m%d%H%M%S")
        except DailyLog.DoesNotExist:
            # raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            daily = DailyLog()
            sign_date = str(0)

        # sign_date = daily.sign_date.strftime("%Y%m%d%H%M%S")
        if sign_date < yesterday_format:  # 判断昨天签到没有
            fate = 1
            daily.number = 1
        else:
            if int(daily.number) == 6:
                fate = daily.number + 1
                daily.number = 0
            else:
                fate = daily.number + 1
                daily.number += 1
        try:
            dailysettings = DailySettings.objects.get(days=fate)
        except DailySettings.DoesNotExist:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        rewards = dailysettings.rewards
        # usercoin = UserCoin.objects.get(user_id=user.id, coin_id=dailysettings.coin)
        user.integral += rewards
        user.save()
        daily.sign_date = time.strftime('%Y-%m-%d %H:%M:%S')
        daily.user_id = user_id
        daily.save()
        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = "积分"
        coin_detail.amount = '+' + str(rewards)
        coin_detail.rest = user.integral
        coin_detail.amount = '+' + str(rewards)
        coin_detail.rest = user.integral
        coin_detail.sources = 7
        coin_detail.save()
        print("daily===================", daily.number)

        content = {'code': 0,
                   'data': rewards
                   }
        return self.response(content)


class MessageListView(ListAPIView, DestroyAPIView):
    """
    通知列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = MessageListSerialize

    def get_queryset(self):
        user = self.request.user.id
        list = UserMessage.objects.filter(Q(user_id=user), Q(status=1) | Q(status=0)).order_by("-created_at")
        return list

    def list(self, request, *args, **kwargs):
        type = kwargs['type']
        user = self.request.user.id
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        system_sign = message_sign(user, 1)
        public_sign = message_sign(user, 2)
        for list in items:
            try:
                types = Message.objects.get(pk=list["message"])
            except Exception:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            if int(types.type) != int(type):
                continue
            data.append({
                "message_id": list["message"],
                'type': list["type"],
                'message_title': list["title"],
                'is_read': list["status"],
                'message_date': list["created_at"],
            })
        return self.response({'code': 0,
                              'data': data,
                              'system_sign': system_sign,
                              'public_sign': public_sign})


class DetailView(ListAPIView):
    """
    获取消息详细内容
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        message_id = kwargs['message_id']
        try:
            message = Message.objects.get(id=message_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = self.request.user.id
        UserMessage.objects.filter(user_id=user, message_id=message_id).update(status=1)
        content = {'code': 0,
                   'data': message.content}
        return self.response(content)


class AllreadView(ListCreateAPIView):
    """
    一键阅读所有消息公告
    """
    permission_classes = (LoginRequired,)

    def post(self, request):
        user_id = self.request.user.id
        UserMessage.objects.filter(user_id=user_id).update(status=1)
        content = {'code': 0}
        return self.response(content)


class AssetView(ListAPIView):
    """
    资产情况
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserCoinSerialize

    def get_queryset(self):
        user = self.request.user.id
        list = UserCoin.objects.filter(user_id=user)
        return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        user = request.user.id
        Progress = results.data.get('results')
        data = []
        try:
            user_info = User.objects.get(id=user)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        for list in Progress:
            print("list['balance']============================", list['balance'])
            print("list['balance']============================", type(list['balance']))
            data.append({
                'icon': list["icon"],
                'coin_name': list["coin_name"],
                'coin': list["coin"],
                'recharge_address': list['address'],
                # 'balance': [str(list['balance']), int(list['balance'])][int(list['balance']) == list['balance']],
                'balance': list['balance'],
                'locked_coin': list['locked_coin'],
                'min_present': list['min_present'],
                'recent_address': list['recent_address']
            })
        return self.response({'code': 0, 'user_name': user_info.username, 'user_avatar': user_info.avatar,
                              'user_integral': user_info.integral, 'data': data})


# class AssetLockView(CreateAPIView):
#     """
#     资产锁定
#     """
#     permission_classes = (LoginRequired,)
#
#     def post(self, request, *args, **kwargs):
#         value = value_judge(request, 'locked_days', 'amounts')
#         if value == 0:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#
#         userid = self.request.user.id
#         userinfo = User.objects.get(id=userid)
#         amounts = request.data.get('amounts')
#         locked_days = request.data.get('locked_days')
#         # passcode = request.data.get('passcode')
#         coin = Coin.objects.get(type=1)
#         try:
#             coin_configs = \
#                 CoinLock.objects.filter(period=locked_days, is_delete=0, Coin_id=coin.id).order_by('-created_at')[0]
#         except Exception:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#
#         # if passcode == '' and int(passcode) != int(userinfo.pass_code):
#         #     raise ParamErrorException(error_code.API_21401_USER_PASS_CODE_ERROR)
#
#         user_coin = UserCoin.objects.get(user_id=userid, coin_id=coin.id)
#         if int(amounts) > int(user_coin.balance) or int(amounts) == 0:
#                 # or int(amounts) > int(coin_configs.limit_end) \
#                 # or int(amounts) < int(coin_configs.limit_start) \
#
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#         user_coin.balance -= int(amounts)
#         user_coin.save()
#         ulcoin = UserCoinLock()
#         ulcoin.user = userinfo
#         ulcoin.amount = int(amounts)
#         ulcoin.coin_lock = coin_configs
#         ulcoin.save()
#         new_log = UserCoinLock.objects.filter(user_id=userid).order_by('-created_at')[0]
#         new_log.end_time = new_log.created_at + timedelta(days=int(locked_days))
#         new_log.save()
#         coin_detail = CoinDetail()
#         coin_detail.user = userinfo
#         coin_detail.coin = user_coin.coin
#         coin_detail.amount = '-'+str(amounts)
#         coin_detail.rest = user_coin.balance
#         coin_detail.sources = 6
#         coin_detail.save()
#         content = {'code': 0}
#         return self.response(content)


class UserPresentationView(CreateAPIView):
    """
    币种提现
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'p_address', 'p_address_name', 'p_amount', 'c_id')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        userid = self.request.user.id
        userinfo = User.objects.get(pk=userid)
        # passcode = request.data.get('passcode')
        p_address = request.data.get('p_address')
        p_address_name = request.data.get('p_address_name')
        c_id = request.data.get('c_id')
        try:
            coin = Coin.objects.get(id=int(c_id))
            user_coin = UserCoin.objects.get(user_id=userid, coin_id=coin.id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        p_amount = eval(request.data.get('p_amount'))

        # if int(passcode) != int(userinfo.pass_code):
        #     raise ParamErrorException(error_code.API_21401_USER_PASS_CODE_ERROR)

        if p_amount > user_coin.balance or p_amount <= 0 or p_amount < coin.cash_control:
            if p_amount > user_coin.balance:
                raise ParamErrorException(error_code.API_70101_USER_PRESENT_AMOUNT_GT)
            elif p_amount < coin.cash_control:
                raise ParamErrorException(error_code.API_70103_USER_PRESENT_AMOUNT_LC)
            else:
                raise ParamErrorException(error_code.API_70102_USER_PRESENT_AMOUNT_EZ)

        address_check = UserPresentation.objects.filter(address=p_address, coin_id=coin.id).order_by('user').values(
            'user').distinct()
        if len(address_check) > 0:
            if len(address_check) > 1 or address_check[0]['user'] != userid or p_address == '':
                if len(address_check) > 1 or address_check[0]['user'] != userid:
                    raise ParamErrorException(error_code.API_70104_USER_PRESENT_ADDRESS_EX)
                else:
                    raise ParamErrorException(error_code.API_70105_USER_PRESENT_ADDRESS_EY)

        if p_address_name == '':
            raise ParamErrorException(error_code.API_70106_USER_PRESENT_ADDRESS_NAME)

        user_coin.balance -= Decimal(p_amount)
        user_coin.save()
        presentation = UserPresentation()
        presentation.user = userinfo
        presentation.coin = coin
        presentation.amount = p_amount
        try:
            presentation.rest = user_coin.balance
        except Exception:
            raise
        presentation.address = p_address
        presentation.address_name = p_address_name
        presentation.save()
        coin_detail = CoinDetail()
        coin_detail.user = userinfo
        coin_detail.coin_name = user_coin.coin.name
        coin_detail.amount = '-' + str(p_amount)
        coin_detail.rest = user_coin.balance
        coin_detail.sources = 2
        coin_detail.save()
        content = {'code': 0}
        return self.response(content)


class PresentationListView(ListAPIView):
    """
    提现记录表
    """
    permission_classes = (LoginRequired,)
    serializer_class = PresentationSerialize

    def get_queryset(self):
        userid = self.request.user.id
        c_id = int(self.kwargs['c_id'])
        try:
            coin = Coin.objects.get(id=c_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        query = UserPresentation.objects.filter(user_id=userid, status=1, coin_id=coin.id)
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for x in items:
            data.append(
                {
                    'id': x['id'],
                    'coin_id': x['coin'],
                    'amount': [str(x['amount']), int(x['amount'])][int(x['amount']) == x['amount']],
                    'rest': [str(x['rest']), int(x['rest'])][int(x['rest']) == x['rest']],
                    'address': x['address'],
                    'created_at': x['created_at'].split(' ')[0].replace('-', '/')
                }
            )
        return self.response({'code': 0, 'data': data})


# class ReviewListView(ListAPIView):
#     """
#     提现审核情况
#     """
#
#     permission_classes = (LoginRequired,)
#     serializer_class = PresentationSerialize
#
#     def get_queryset(self):
#         userid = self.request.user.id
#         c_id = int(self.kwargs['c_id'])
#         if c_id <= 1:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#         try:
#             coin = Coin.objects.get(id=c_id)
#         except Exception:
#             raise
#         query = UserPresentation.objects.filter(user_id=userid, coin_id=coin.id)
#         return query
#
#     def list(self, request, *args, **kwargs):
#         results = super().list(request, *args, **kwargs)
#         items = results.data.get('results')
#         data = []
#         STATUS = ["申请中", "已处理", "已拒绝"]
#         for x in items:
#             data.append(
#                 {
#                     'id': x['id'],
#                     'coin_id': x['coin'],
#                     'amount': x['amount'],
#                     'status': STATUS[x['status']],
#                     'status_code': x['status'],
#                     'created_at': x['created_at'].split(' ')[0].replace('-','/')
#                 }
#             )
#         return self.response({'code': 0, 'data': data})
#

# class LockListView(ListAPIView):
#     """
#     锁定记录
#     """
#     permission_classes = (LoginRequired,)
#     serializer_class = AssetSerialize
#
#     def get_queryset(self):
#         userid = self.request.user.id
#         query = UserCoinLock.objects.filter(user_id=userid)
#         return query
#
#     def list(self, request, *args, **kwargs):
#         results = super().list(request, *args, **kwargs)
#         items = results.data.get('results')
#         data = []
#         for x in items:
#             # if x['end_time'] >= x['created_at']:
#             data.append(
#                 {
#
#                     'id': x['id'],
#                     'created_at': x['created_at'].split(' ')[0].replace('-','/'),
#                     'amount': x['amount'],
#                     'time_delta': x['time_delta']
#                 }
#             )
#         return self.response({'code': 0, 'data': data})


# class DividendView(ListAPIView):
#     """
#     锁定金额分红记录
#     """
#
#     permission_classes = (LoginRequired,)
#     serializer_class = AssetSerialize
#
#     def get_queryset(self):
#         userid = self.request.user.id
#         # now = datetime.now()
#         query = UserCoinLock.objects.filter(user_id=userid, is_free=1)  # USE_TZ = True时,可直接用now比较,否则now=datetime.utcnow()
#         return query
#
#     def list(self, request, *args, **kwargs):
#         results = super().list(request, *args, **kwargs)
#         items = results.data.get('results')
#         # now = datetime.now()
#         data = []
#         for x in items:
#             # end_time = datetime.strptime(x['end_time'], '%Y-%m-%dT%H:%M:%S+08:00')
#             # if now > end_time:
#             dividend = int(x['amount']) * float(x['profit'])
#             data.append(
#                 {
#                     'id': x['id'],
#                     'amount': x['amount'],
#                     'period': x['period'],
#                     'dividend': round(dividend, 2),
#                     'created_at': x['created_at'].split(' ')[0].replace('-','/'),
#                     'end_time': x['end_time'].split(' ')[0].replace('-','/')
#                 }
#             )
#         return self.response({'code': 0, 'data': data})


class SettingOthersView(ListAPIView):
    """
    用户设置其他
    """
    permission_classes = (LoginRequired,)

    def list(self, request, *args, **kwargs):
        r_type = int(request.user.register_type)
        try:
            index = kwargs['index']
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) not in range(1, 5):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            data = UserSettingOthors.objects.get(reg_type=r_type)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if index == 1:
            return self.response({'code': 0, 'data': data.about})
        elif index == 2:
            return self.response({'code': 0, 'data': data.helps})
        elif index == 3:
            return self.response({'code': 0, 'data': data.sv_contractus})
        else:
            return self.response({'code': 0, 'data': data.sv_contractus})


class RegisterView(CreateAPIView):
    """
    用户注册
    """

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')
        telephone = request.data.get('username')
        code = request.data.get('code')
        password = request.data.get('password')

        # 校验手机短信验证码
        message = Sms.objects.filter(telephone=telephone, code=code, type=Sms.REGISTER)
        if len(message) == 0:
            return self.response({
                'code': error_code.API_20402_INVALID_SMS_CODE
            })

        # 判断该手机号码是否已经注册
        user = User.objects.filter(username=telephone)
        if len(user) > 0:
            return self.response({
                'code': error_code.API_20102_TELEPHONE_REGISTERED
            })

        # 用户注册
        ur = UserRegister()
        avatar = settings.STATIC_DOMAIN_HOST + "/images/avatar.png"
        token = ur.register(source=source, username=telephone, password=password, avatar=avatar, nickname=telephone)
        return self.response({
            'code': error_code.API_0_SUCCESS,
            'data': {
                'access_token': token
            }
        })


class CoinTypeView(CreateAPIView, ListAPIView):
    """
    # get:币种切换列表
    post：币种切换
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserCoinSerialize

    def get_queryset(self):
        user_id = self.request.user.id
        try:
            index = self.request.parser_context['kwargs']['index']
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) not in range(1, 3):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if index == 1:
            query = UserCoin.objects.filter(~(Q(coin__type=1) | Q(is_opt=1)), user_id=user_id, balance__gt=0)  # 首页
        elif index == 2:
            query = UserCoin.objects.filter(user_id=user_id, balance__gt=0)  # 下注
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        try:
            index = kwargs['index']
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) not in range(1, 3):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) == 1:
            for i in items:
                data.append(
                    {
                        'id': i['id'],
                        'name': i['name'],
                        'coin_name': i['coin_name'],
                        'icon': i['icon'],
                        'total': i['total'],
                        'coin': i['coin'],
                        'coin_value': i['coin_value']
                    }
                )
        elif int(index) == 2:
            for i in items:
                data.append(
                    {
                        'id': i['id'],
                        'name': i['name'],
                        'icon': i['icon'],
                        'balance': i['balance'],
                        'coin_value': i['coin_value']
                    }
                )
        return self.response({'code': 0, 'data': data})

    def post(self, request, *args, **kwargs):
        userid = self.request.user.id
        value = value_judge(request, 'new_coin')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        new_coin = request.data.get('new_coin')
        try:
            used = UserCoin.objects.get(user_id=userid, is_opt=1)
            useds = UserCoin.objects.get(user_id=userid, is_bet=1)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            new = UserCoin.objects.get(pk=new_coin)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            index = kwargs['index']
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) not in range(1, 3):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if int(index) == 1:
            used.is_opt = 0
            new.is_opt = 1
            used.save()
        elif int(index) == 2:
            useds.is_bet = 0
            new.is_bet = 1
            useds.save()
        new.save()
        content = {'code': 0}
        return self.response(content)


class ForgetPasswordView(ListAPIView):
    """
    修改密码
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "password", "code", "username")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        password = request.data.get('password')
        username = request.data.get('username')
        try:
            userinfo = User.objects.get(username=username)
        except Exception:
            raise ParamErrorException(error_code.API_20103_TELEPHONE_UNREGISTER)

        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(telephone=userinfo.telephone).order_by('-id').first()
        if (sms is None) or (sms.code != request.data.get('code')):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})

        if int(sms.type) != 5:
            return self.response({'code': error_code.API_40106_SMS_PARAMETER})

        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.now().timetuple())
        if current_time - time.mktime(sent_time.timetuple()) >= settings.SMS_CODE_EXPIRE_TIME:
            return self.response({'code': error_code.API_20403_SMS_CODE_EXPIRE})

        if len(password) < 6:
            raise ParamErrorException(error_code=error_code.API_20802_PASS_CODE_LEN_ERROR)
        if "password" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20801_PASS_CODE_ERROR)

        userinfo.set_password(password)
        userinfo.save()
        content = {'code': 0}
        return self.response(content)


class UserRechargeView(ListCreateAPIView):
    """
    用户充值
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        index = kwargs.get('index')
        if 'recharge' not in request.data or 'r_address' not in request.data:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        recharge = int(request.data.get('recharge'))
        r_address = request.data.get('r_address')
        if not r_address:
            raise ParamErrorException(error_code.API_70201_USER_RECHARGE_ADDRESS)
        if recharge <= 0:
            raise ParamErrorException(error_code.API_70202_USER_RECHARGE_AMOUNT)
        uuid = request.user.id
        try:
            user_coin = UserCoin.objects.get(id=index, user_id=uuid)
        except Exception:
            raise
        user_coin.balance += Decimal(recharge)
        user_coin.save()
        user_recharge = UserRecharge(user_id=uuid, coin_id=index, amount=recharge, address=r_address)
        user_recharge.save()
        coin_detail = CoinDetail(user_id=uuid, coin_name=user_coin.coin.name, amount='+' + str(recharge),
                                 rest=user_coin.balance, sources=1)
        coin_detail.save()
        return self.response({'code': 0})


class CoinOperateView(ListAPIView):
    """
    充值和提现记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = CoinOperateSerializer

    def get_queryset(self):
        try:
            coin = Coin.objects.get(id=self.kwargs['coin'])
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        uuid = self.request.user.id
        query_s = CoinDetail.objects.filter(user_id=uuid, sources__in=[1, 2], coin_name=coin.name).order_by(
            '-created_at')
        return query_s

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        temp_dict = {}
        for x in items:
            if x['month'] not in temp_dict:
                x['top'] = True
                temp_dict[x['month']] = [x, ]
            else:
                temp_dict[x['month']].append(x)
        temp_list = []
        for x in temp_dict:
            item = {'year': x, 'items': temp_dict[x]}
            temp_list.append(item)

        return self.response({'code': 0, 'data': temp_list})


class CoinOperateDetailView(RetrieveAPIView):
    """
    充值和提现记录明细
    """
    permission_classes = (LoginRequired,)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']
        try:
            coin = Coin.objects.get(id=self.kwargs['coin'])
            item = CoinDetail.objects.get(id=pk, coin_name=coin.name)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        serialize = CoinOperateSerializer(item)
        return self.response({'code': 0, 'data': serialize.data})


class VersionUpdateView(RetrieveAPIView):
    """
    版本更新
    """

    def retrieve(self, request, *args, **kwargs):
        version = request.query_params.get('version')
        try:
            last_version = AndroidVersion.objects.filter(is_delete=0).order_by('-create_at')[0]
        except last_version.DoesNotExist:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if last_version.version == version:
            return self.response({'code': 0, 'is_new': 0})
        else:
            serialize = AndroidSerializer(last_version)
            return self.response({'code': 0, 'is_new': 1, 'data': serialize.data})


class ImageUpdateView(CreateAPIView):
    """
    更换上传头像
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        form = ImageForm(request.POST, request.FILES)
        safe_image_type = request.FILES['image'].name.strip().split('.')[-1] in ('jpg', 'png', 'jpeg')
        # temp_img = None
        if safe_image_type:
            if form.is_valid():
                new_doc = Im(image=request.FILES['image'])
                new_doc.save()
                temp_img = new_doc
            else:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        else:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if temp_img == None:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        image_path = temp_img.image.path
        resize_img(image_path, 300, 300)  # 图片等比压缩
        uuid = request.user.id
        try:
            user = User.objects.get(pk=uuid)
        except Exception:
            raise
        image_name = temp_img.image.name
        avatar_url = ''.join([MEDIA_DOMAIN_HOST, '/', image_name])
        user.avatar = avatar_url
        user.save()
        return self.response({'code': 0, 'data': avatar_url})


class InvitationRegisterView(CreateAPIView):
    """
    用户邀请注册
    """

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')
        invitation_id = request.data.get('invitation_id')
        telephone = request.data.get('telephone')
        code = request.data.get('code')
        password = request.data.get('password')

        # 校验手机短信验证码
        message = Sms.objects.filter(telephone=telephone, code=code, type=Sms.REGISTER)
        if len(message) == 0:
            return self.response({
                'code': error_code.API_20402_INVALID_SMS_CODE
            })

        # 判断该手机号码是否已经注册
        user = User.objects.filter(username=telephone)
        if len(user) > 0:
            return self.response({
                'code': error_code.API_20102_TELEPHONE_REGISTERED
            })
        all_money = UserInvitation.objects.filter(is_deleted=1).aggregate(Sum('money'))
        all_money = all_money['money__sum']  # 获得总钱数
        if all_money is not None:
            all_money += 100
            if all_money > 200000000:
                raise ParamErrorException(error_code.API_60101_USER_INVITATION_MONEY)

        # 用户注册
        ur = UserRegister()
        avatar = settings.STATIC_DOMAIN_HOST + "/images/avatar.png"
        token = ur.register(source=source, username=telephone, password=password, avatar=avatar, nickname=telephone)
        invitee_one = UserInvitation.objects.filter(invitee_one=int(invitation_id)).count()
        try:
            user_info = User.objects.get(pk=invitation_id)
        except DailyLog.DoesNotExist:
            return 0
        if invitee_one > 0:
            try:
                invitee = UserInvitation.objects.get(invitee_one=int(invitation_id))
            except DailyLog.DoesNotExist:
                return 0
            on_line = invitee.inviter
            invitee_number = UserInvitation.objects.filter(~Q(invitee_two=0), inviter_id=on_line,
                                                           is_deleted=1).count()
            user_on_line = UserInvitation()
            if invitee_number < 100:
                user_on_line.is_effective = 1
                user_on_line.money = 50
            user_on_line.inviter = on_line
            user_on_line.invitee_two = user_info.id
            user_on_line.save()
        user_go_line = UserInvitation()
        invitee_number = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=int(invitation_id),
                                                       is_deleted=1).count()
        if invitee_number < 10:
            user_go_line.is_effective = 1
            user_go_line.money = 200

        user_go_line.inviter = user_info
        user_go_line.invitee_one = user_info.id
        user_go_line.save()
        return self.response({
            'code': error_code.API_0_SUCCESS,
            'data': {
                'access_token': token
            }
        })


class InvitationInfoView(ListAPIView):
    """
    用户邀请信息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        invitation_one_number = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=user_id).count()  # T1总人数
        invitation_two_number = UserInvitation.objects.filter(~Q(invitee_two=0), inviter=user_id).count()  # T2总人数
        user_invitation_one = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=user_id, is_deleted=1).aggregate(
            Sum('money'))
        user_invitation_two = UserInvitation.objects.filter(~Q(invitee_two=0), inviter=user_id, is_deleted=1).aggregate(
            Sum('money'))
        user_invitation_ones = user_invitation_one['money__sum']  # T1获得总钱数
        if user_invitation_ones == None:
            user_invitation_ones = 0
        user_invitation_twos = user_invitation_two['money__sum']  # T2获得总钱数
        if user_invitation_twos == None:
            user_invitation_twos = 0
        moneys = int(user_invitation_ones) + int(user_invitation_twos)  # 获得总钱数
        return self.response(
            {'code': 0, 'invitation_one_number': invitation_one_number, 'invitation_two_number': invitation_two_number,
             'user_invitation_one': user_invitation_ones, 'user_invitation_twos': user_invitation_twos,
             'moneys': moneys})


class InvitationUserView(ListAPIView):
    """
    扫描二维码拿用户消息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')
        try:
            user_info = User.objects.get(pk=user_id)
        except DailyLog.DoesNotExist:
            return 0
        nickname = user_info.nickname
        avatar = user_info.avatar
        username = user_info.username
        return self.response({'code': 0, "nickname": nickname, "avatar": avatar, "username": username})


class InvitationUrlMergeView(ListAPIView):
    """
    生成用户推广URL
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        qr_data = settings.SITE_DOMAIN + '/invitation/user/?user_id=' + str(user_id)
        return self.response({'code': 0, "qr_data": qr_data})


class InvitationMergeView(ListAPIView):
    """
    生成用户推广页面
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        sub_path = str(user_id % 10000)
        base_img = Image.open(settings.BASE_DIR + '/uploads/fx_bk.png')
        qr_data = settings.SITE_DOMAIN + '/invitation/user/?user_id=' + str(user_id)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()
        base_img.paste(qr_img, (226, 770))

        spread_path = settings.MEDIA_ROOT + 'spread/'
        if not os.path.exists(spread_path):
            os.mkdir(spread_path)

        save_path = spread_path + sub_path
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        # 保存二维码图片
        qr_img.save(save_path + '/qrcode_' + str(user_id) + '.png', 'PNG')
        qr_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/qrcode_' + str(user_id) + '.png'

        # 保存推广图片
        base_img.save(save_path + '/spread_' + str(user_id) + '.png', 'PNG', quality=90)
        base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user_id) + '.png'

        return self.response({'code': 0, "qr_img": qr_img, "base_img": base_img})


class LuckDrawListView(ListAPIView):
    """
    奖品列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = LuckDrawSerializer

    def get_queryset(self):
        prize_list = IntegralPrize.objects.filter(is_delete=0)
        return prize_list

    def list(self, request, *args, **kwargs):
        user_id = request.user.id
        cache = caches['redis']
        date = datetime.now().strftime('%Y%m%d')
        NUMBER_OF_LOTTERY_AWARDS = "number_of_lottery_Awards_" + str(user_id) + str(date)  # 再来一次次数
        awards_number = cache.get(NUMBER_OF_LOTTERY_AWARDS)
        NUMBER_OF_PRIZES_PER_DAY = "number_of_prizes_per_day_" + str(user_id) + str(date)  # 每天抽奖次数
        number = cache.get(NUMBER_OF_PRIZES_PER_DAY)
        if number == None:
            number = 6
            cache.set(NUMBER_OF_PRIZES_PER_DAY, number, 24 * 3600)
            number = cache.get(NUMBER_OF_PRIZES_PER_DAY)
        is_gratis = 0
        if awards_number == None:
            is_gratis = 0
        elif awards_number > 0:
            is_gratis = 1
        if number == 6:
            is_gratis = 1
        cache.set(NUMBER_OF_LOTTERY_AWARDS, is_gratis, 24 * 3600)
        user = request.user
        results = super().list(request, *args, **kwargs)
        list = results.data.get('results')
        data = []
        for x in list:
            data.append(
                {
                    'user_id': user_id,
                    'id': x['id'],
                    'prize_name': x['prize_name'],
                    'icon': x['icon'],
                    'prize_number': x['prize_number'],
                    'created_at': x['created_at'],
                    'prize_weight': x['prize_weight']
                }
            )
        return self.response(
            {'code': 0, 'data': data, 'is_gratis': is_gratis, 'number': number, 'integral': user.integral,
             'prize_consume': list[0]['prize_consume']})


class ClickLuckDrawView(CreateAPIView):
    """
    点击抽奖
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        cache = caches['redis']
        user_info = request.user
        date = datetime.now().strftime('%Y%m%d')
        NUMBER_OF_LOTTERY_AWARDS = "number_of_lottery_Awards_" + str(user_info.pk) + str(date)  # 再来一次次数
        is_gratis = cache.get(NUMBER_OF_LOTTERY_AWARDS)
        NUMBER_OF_PRIZES_PER_DAY = "number_of_prizes_per_day_" + str(user_info.pk) + str(date)  # 每天抽奖次数
        number = cache.get(NUMBER_OF_PRIZES_PER_DAY)
        number = int(number)
        if is_gratis != 1 and user_info.integral < 20:
            raise ParamErrorException(error_code=error_code.API_60103_INTEGRAL_INSUFFICIENT)
        if int(number) <= 0 and is_gratis != 1:
            raise ParamErrorException(error_code=error_code.API_60102_LUCK_DRAW_FREQUENCY_INSUFFICIENT)
        prize = []
        prize_weight = []
        prize_list = IntegralPrize.objects.filter(is_delete=0).values_list('prize_name', 'prize_weight')
        for list in prize_list:
            prize_weight.append(int(list[1]) * 1000)
            prize.append(list[0])
        choice = prize[weight_choice(prize_weight)]
        if int(is_gratis) == 1 and int(number) == 6:
            print("第一次")
            is_gratis = 0
            cache.set(NUMBER_OF_LOTTERY_AWARDS, is_gratis)
            number -= 1
            cache.set(NUMBER_OF_PRIZES_PER_DAY, int(number))
        elif int(is_gratis) == 1:
            print("再来一次")
            is_gratis = 0
            cache.set(NUMBER_OF_LOTTERY_AWARDS, is_gratis)
        elif int(is_gratis) != 1 and int(number) != 6:
            print("继续抽奖")
            number -= 1
            cache.set(NUMBER_OF_PRIZES_PER_DAY, int(number))
            is_gratis = 0
            cache.set(NUMBER_OF_LOTTERY_AWARDS, is_gratis)
            user_info.integral -= 20
            user_info.save()
        try:
            integral_prize = IntegralPrize.objects.get(prize_name=choice)
        except DailyLog.DoesNotExist:
            return 0
        if choice == "再来一次":
            is_gratis = 1
            cache.set(NUMBER_OF_LOTTERY_AWARDS, is_gratis, 24 * 3600)
        if choice == "积分":
            user_info.integral += int(integral_prize.prize_number)
            user_info.save()
        fictitious_prize_name_list = IntegralPrize.objects.filter(is_delete=0, is_fictitious=1).values_list(
            'prize_name')
        fictitious_prize_name = []
        for a in fictitious_prize_name_list:
            fictitious_prize_name.append(a[0])

        if choice in fictitious_prize_name:
            coin = Coin.objects.filter(name=choice)
            coin = coin[0]
            try:
                user_coin = UserCoin.objects.get(user_id=user_info.pk, coin_id=coin.id)
            except DailyLog.DoesNotExist:
                return 0
            coin_detail = CoinDetail()
            coin_detail.user = user_info
            coin_detail.coin_name = choice
            coin_detail.amount = int(integral_prize.prize_number)
            coin_detail.rest = int(user_coin.balance)
            coin_detail.sources = 4
            coin_detail.save()
            user_coin.balance += int(integral_prize.prize_number)
            user_coin.save()

        integral_prize_record = IntegralPrizeRecord()
        integral_prize_record.user = user_info
        integral_prize_record.prize = integral_prize
        integral_prize_record.is_receive = 1
        integral_prize_record.save()
        prize_number = integral_prize.prize_number
        if int(integral_prize.prize_number) == 0:
            prize_number = ""
        return self.response({
            'code': 0,
            'data': {
                'id': integral_prize.id,
                'icon': integral_prize.icon,
                'prize_name': integral_prize.prize_name,
                'prize_number': prize_number,
                'integral': user_info.integral,
                'number': cache.get(NUMBER_OF_PRIZES_PER_DAY),
                'is_gratis': cache.get(NUMBER_OF_LOTTERY_AWARDS)
            }
        })
