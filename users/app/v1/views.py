# -*- coding: UTF-8 -*-
from django.db.models import Q
from .serializers import UserInfoSerializer, UserSerializer, DailySerialize, MessageListSerialize, \
    PresentationSerialize, UserCoinSerialize, CoinOperateSerializer, LuckDrawSerializer, LockSerialize, \
    CountriesSerialize, UserRechargeSerizlize, HomeMessageSerialize
import qrcode
from django.core.cache import caches
from quiz.models import Quiz, Record
from ...models import User, DailyLog, DailySettings, UserMessage, Message, \
    UserPresentation, UserCoin, Coin, UserRecharge, CoinDetail, \
    UserSettingOthors, UserInvitation, IntegralPrize, IntegralPrizeRecord, LoginRecord, \
    CoinOutServiceCharge, BankruptcyRecords, CoinGive, CoinGiveRecords, IntInvitation, CoinLock, \
    UserCoinLock, Countries, Dividend
from chat.models import Club
from console.models import Address
from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView
from base.function import LoginRequired
from base.function import randomnickname, weight_choice
from sms.models import Sms
from datetime import timedelta, datetime, date
import time
import pytz
from decimal import Decimal
from django.conf import settings
from base import code as error_code
from base.exceptions import ParamErrorException, UserLoginException
from utils.functions import random_salt, sign_confirmation, message_hints, language_switch, \
    message_sign, resize_img, normalize_fraction, random_invitation_code, \
    coin_initialization
from rest_framework_jwt.settings import api_settings
from django.db import transaction
import linecache
import re
import os
import pygame
from pygame.locals import *
from config.models import AndroidVersion
from config.serializers import AndroidSerializer
from utils.forms import ImageForm
from utils.models import Image as Im
from api.settings import MEDIA_DOMAIN_HOST, BASE_DIR
from django.db.models import Sum
from PIL import Image
from utils.cache import set_cache, get_cache, decr_cache, incr_cache, delete_cache
from utils.functions import value_judge, get_sql
import requests
import json
from captcha.models import CaptchaStore


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

    @staticmethod
    def get_user(username):
        """
        获取用户对象
        :param username:
        :return:
        """
        user = None
        user_name_exists = User.objects.filter(username=username).count()
        if user_name_exists > 0:
            user = User.objects.get(username=username)
        else:
            user = User.objects.get(telephone=username)

        return user

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

    def login(self, source, username, area_code, password, device_token=''):
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
            if user.is_block == 1:
                raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)
            token = self.get_access_token(source=source, user=user)
        else:
            try:
                if area_code is None:
                    area_code = 86
                user = User.objects.get(area_code=area_code, username=username)
            except Exception:
                raise ParamErrorException(error_code.API_10105_NO_REGISTER)
            if user.is_block == 1:
                raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)
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

            coins = Coin.objects.filter(is_disabled=False)  # 生成货币余额与充值地址
            for coin in coins:
                user_id = user.id
                coin_id = coin.id
                coin_initialization(user_id, coin_id)

            # 更新用户的device_token
            if device_token is not None and device_token != '':
                user.device_token = device_token
                user.save()

            # 注册送HAND币
            if user.is_money == 0 and user.is_robot == 0:
                user_money = 10000
                try:
                    user_balance = UserCoin.objects.get(coin__name='HAND', user_id=user.id)
                except Exception:
                    return 0
                user_balance.balance += user_money
                user_balance.save()
                coin_detail = CoinDetail()
                coin_detail.user = user
                coin_detail.coin_name = 'HAND'
                coin_detail.amount = '+' + str(user_money)
                coin_detail.rest = Decimal(user_balance.balance)
                coin_detail.sources = 6
                coin_detail.save()
                user.is_money = 1
                user.save()
                r_msg = UserMessage()  # 注册送hand消息
                r_msg.status = 0
                r_msg.user = user
                r_msg.message_id = 5
                r_msg.save()
        return token

    @transaction.atomic()
    def register(self, source, username, password, device_token='', area_code='', avatar='', nickname='',
                 invitation_code='', ip_address=''):
        """
        用户注册
        :param source:      用户来源：ios、android
        :param username:    用户账号：openid
        :param password     登录密码
        :param area_code     手机区号
        :param avatar:      用户头像，第三方登录提供
        :param nickname:    用户昵称，第三方登录提供
        :return:
        """
        # 根据username的长度判断注册type
        # 11 telephone
        # 32 QQ
        # 28 微信
        # 邀请码注册

        if invitation_code != '':  # 是否用邀请码注册
            invitation_user = User.objects.get(invitation_code=invitation_code)
            inviter_number = UserInvitation.objects.filter(inviter_id=int(invitation_user.pk),
                                                           is_effective=1, coin=9).count()

            register_type = self.get_register_type(username)
            user = User()
            if len(username) == 11:
                user.telephone = username
            if area_code is None or area_code == '':
                area_code = 86
            user.area_code = area_code
            user.username = username
            user.source = user.__getattribute__(source.upper())
            user.set_password(password)
            user.register_type = register_type
            user.ip_address = ip_address
            user.avatar = avatar
            user.nickname = nickname
            user.device_token = device_token
            user.invitation_code = random_invitation_code()
            user.save()

            give_info = CoinGive.objects.get(pk=1)  # 货币赠送活动
            end_date = give_info.end_time.strftime("%Y%m%d%H%M%S")
            today = date.today()
            today_time = today.strftime("%Y%m%d%H%M%S")
            user_go_line = UserInvitation()  # 邀请T1是否已达上限
            if inviter_number < 5 and today_time < end_date and invitation_user.is_robot == False:
                user_go_line.is_effective = 1
                user_go_line.money = 3888
                user_go_line.is_robot = False
            user_go_line.inviter = invitation_user
            user_go_line.invitation_code = invitation_code
            user_go_line.invitee_one = user.id
            user_go_line.save()

            invitee_one = UserInvitation.objects.filter(invitee_one=int(invitation_user.pk)).count()
            if invitee_one > 0:  # 邀请人为他人T1.
                try:
                    invitee = UserInvitation.objects.filter(invitee_one=int(invitation_user.pk)).first()
                except DailyLog.DoesNotExist:
                    return 0
                on_line = invitee.inviter
                invitee_number = UserInvitation.objects.filter(~Q(invitee_two=0), inviter_id=on_line,
                                                               is_effective=1, coin=4).count()
                user_on_line = UserInvitation()  # 邀请T2是否已达上限
                if invitee_number < 10 and on_line.is_robot == False:
                    user_on_line.is_effective = 1
                    user_on_line.money = 2000
                    user_go_line.is_robot = False
                user_on_line.inviter = on_line
                user_on_line.invitee_two = user.id
                user_on_line.save()
        else:
            register_type = self.get_register_type(username)
            user = User()

            user.telephone = username
            if area_code is None:
                area_code = 86
            user.area_code = area_code
            user.username = username
            user.source = user.__getattribute__(source.upper())
            user.set_password(password)
            user.ip_address = ip_address
            user.register_type = register_type
            user.avatar = avatar
            user.nickname = nickname
            user.device_token = device_token
            user.invitation_code = random_invitation_code()
            user.save()

        # 生成签到记录
        try:
            userinfo = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        daily = DailyLog()
        daily.user_id = userinfo.id
        daily.number = 0
        yesterday = datetime.today() + timedelta(-1)
        daily.sign_date = yesterday.strftime("%Y-%m-%d %H:%M:%S")
        daily.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        daily.save()

        coins = Coin.objects.filter(is_disabled=False)  # 生成货币余额与充值地址

        for coin in coins:
            user_id = userinfo.id
            coin_id = coin.id
            coin_initialization(user_id, coin_id)

        give_info = CoinGive.objects.get(pk=1)  # 货币赠送活动
        end_date = give_info.end_time.strftime("%Y%m%d%H%M%S")
        today = date.today()
        today_time = today.strftime("%Y%m%d%H%M%S")
        if today_time < end_date:  # 活动期间
            user_coin = UserCoin.objects.filter(coin_id=give_info.coin_id, user_id=userinfo.id).first()
            user_coin_give_records = CoinGiveRecords()
            user_coin_give_records.start_coin = user_coin.balance
            user_coin_give_records.user = user
            user_coin_give_records.coin_give = give_info
            user_coin_give_records.lock_coin = give_info.number
            user_coin_give_records.save()
            user_coin.balance += give_info.number
            user_coin.save()
            user_message = UserMessage()
            user_message.status = 0
            user_message.user = user
            user_message.message_id = 11
            user_message.save()
            coin_bankruptcy = CoinDetail()
            coin_bankruptcy.user = user
            coin_bankruptcy.coin_name = 'USDT'
            coin_bankruptcy.amount = '+' + str(give_info.number)
            coin_bankruptcy.rest = Decimal(user_coin.balance)
            coin_bankruptcy.sources = 4
            coin_bankruptcy.save()
        if invitation_code != '':  # 是否用邀请码注册
            invitation_user = User.objects.get(invitation_code=invitation_code)
            if int(invitation_user.pk) == 2638:  # INT邀请活动
                invitation_number = IntInvitation.objects.filter(is_block=0).count()
                int_invitation = IntInvitation()
                int_invitation.invitee = userinfo.id
                int_invitation.inviter = invitation_user
                int_invitation.coin = 1
                int_invitation.invitation_code = invitation_code
                if invitation_number >= 2000:
                    int_invitation.money = 0
                    int_invitation.is_deleted = False
                int_invitation.save()
                user_message = UserMessage()
                user_message.status = 0
                user_message.user = user
                user_message.message_id = 13
                user_message.save()
                if int_invitation.money > 0:
                    int_user_coin = UserCoin.objects.get(user_id=user.pk, coin_id=1)
                    int_user_coin.balance += Decimal(int_invitation.money)
                    int_user_coin.save()
                    coin_bankruptcy = CoinDetail()
                    coin_bankruptcy.user = user
                    coin_bankruptcy.coin_name = 'INT'
                    coin_bankruptcy.amount = '+' + str(int_invitation.money)
                    coin_bankruptcy.rest = Decimal(int_user_coin.balance)
                    coin_bankruptcy.sources = 4
                    coin_bankruptcy.save()
        # 生成客户端加密串
        token = self.get_access_token(source=source, user=user)

        return token


class LoginView(CreateAPIView):
    """
    用户登录:
    用户已经注册-----》登录
    新用户---------》注册----》登录
    """

    def get_name_avatar(self):
        """
        获取已经下载的用户昵称和头像
        :return:
        """
        key_name_avatar = 'new_avatar_key'

        line_number = get_cache(key_name_avatar)
        file_avatar_nickname = settings.CACHE_DIR + '/new_avatar.lst'
        if line_number is None:
            line_number = 1

        avatar_nickname = linecache.getline(file_avatar_nickname, line_number)
        a = avatar_nickname.split('_')
        if len(a) > 2:
            folder = str(a[0])
            suffix = str(a[1]) + "_" + str(a[2])
        else:
            folder, suffix = avatar_nickname.split('_')

        avatar_url = settings.MEDIA_DOMAIN_HOST + "/avatar/" + folder + '/' + avatar_nickname

        line_number += 1
        set_cache(key_name_avatar, line_number)
        myfile = open(file_avatar_nickname)
        lines = len(myfile.readlines())
        if line_number >= lines:
            delete_cache(key_name_avatar)
        return avatar_url

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')
        ur = UserRegister()
        value = value_judge(request, "username", "type")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        username = request.data.get('username')
        ip_address = request.META.get("REMOTE_ADDR", '')
        # register_type = ur.get_register_type(username)
        register_type = User.REGISTER_TELEPHONE

        # 校验google recaptcha
        # if 'recaptcha' not in request.data:
        #     raise ParamErrorException(error_code.API_20105_GOOGLE_RECAPTCHA_FAIL)
        # recaptcha = request.data.get('recaptcha')
        # recaptcha_data = {
        #     'secret': '6LcKRlwUAAAAANrxoU9dyYO68fTr_9aXOOYVT-ta',
        #     'response': recaptcha,
        #     'remoteip': ip_address,
        # }
        # result = requests.post('https://www.google.com/recaptcha/api/siteverify', data=recaptcha_data)
        # res = json.loads(result.content.decode('utf-8'))
        # if res is False:
        #     raise ParamErrorException(error_code.API_20105_GOOGLE_RECAPTCHA_FAIL)

        type = request.data.get('type')  # 1 注册          2 登录
        regex = re.compile(r'^(1|2)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

        # 图形验证码，目前只限于HTML5 - 登录请求
        if int(type) == 2:
            captcha_valid_code = User.objects.captcha_valid(request)
            if captcha_valid_code > 0:
                raise ParamErrorException(captcha_valid_code)

        device_token = ""
        if 'device_token' in request.data:
            device_token = request.data.get('device_token')

        user = User.objects.filter(username=username)
        if len(user) == 0:
            avatar = self.get_name_avatar()
            if 'avatar' in request.data:
                avatar = request.data.get('avatar')
            # # 判断同一IP地址是否重复注册
            # ip1, ip2, ip3, ip4 = ip_address.split('.')
            # startswith = ip1 + '.' + ip2 + '.' + ip3 + '.'
            # ip_users = User.objects.filter(ip_address__startswith=startswith).count()
            # if ip_users > 2:
            #     raise ParamErrorException(error_code.API_20404_SAME_IP_ERROR)

            if int(type) == 2:
                raise ParamErrorException(error_code.API_10105_NO_REGISTER)
            nickname = str(username[0:3]) + "***" + str(username[7:])
            if int(register_type) == 1 or int(register_type) == 2:
                password = random_salt(8)
                token = ur.register(source=source, nickname=nickname, username=username, avatar=avatar,
                                    password=password, device_token=device_token, ip_address=ip_address)

            else:
                code = request.data.get('code')
                if 'area_code' not in request.data:
                    area_code = 86
                else:
                    area_code = request.data.get('area_code')
                invitation_code = ''
                if 'invitation_code' in request.data:
                    invitation_code = request.data.get('invitation_code')
                    invitation_code = invitation_code.upper()

                record = Sms.objects.filter(area_code=area_code, telephone=username).order_by(
                    '-id').first()
                if int(record.degree) >= 5:
                    raise ParamErrorException(error_code.API_40107_SMS_PLEASE_REGAIN)
                else:
                    record.degree += 1
                    record.save()

                message = Sms.objects.filter(telephone=username, area_code=area_code, code=code, type=Sms.REGISTER)
                if len(message) == 0:
                    raise ParamErrorException(error_code.API_20402_INVALID_SMS_CODE)

                password = request.data.get('password')
                token = ur.register(source=source, nickname=nickname, username=username, area_code=area_code,
                                    avatar=avatar, device_token=device_token,
                                    password=password, invitation_code=invitation_code, ip_address=ip_address)
        else:
            if int(type) == 1:
                raise ParamErrorException(error_code.API_10106_TELEPHONE_REGISTER)
            if int(register_type) == 1 or int(register_type) == 2:
                password = None
                token = ur.login(source=source, username=username, device_token=device_token, password=password)
            elif int(register_type) == 3:
                password = ''
                # area_code = request.data.get('area_code')
                if 'area_code' not in request.data:
                    area_code = 86
                else:
                    area_code = request.data.get('area_code')
                if 'password' in request.data:
                    password = request.data.get('password')
                token = ur.login(source=source, username=username, device_token=device_token, area_code=area_code,
                                 password=password)
            else:
                password = request.data.get('password')
                # area_code = request.data.get('area_code')
                if 'area_code' not in request.data:
                    area_code = 86
                else:
                    area_code = request.data.get('area_code')
                token = ur.login(source=source, username=username, device_token=device_token, area_code=area_code,
                                 password=password)
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
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user_id = self.request.user.id
        is_sign = sign_confirmation(user_id)  # 是否签到
        clubinfo = Club.objects.get(pk=roomquiz_id)
        coin_name = clubinfo.coin.name
        coin_id = clubinfo.coin.pk

        lr = LoginRecord()  # 登录记录
        lr.user = user
        lr.login_type = request.META.get('HTTP_X_API_KEY', '')
        lr.ip = request.META.get("REMOTE_ADDR", '')
        lr.save()

        message = Message.objects.filter(type=1, created_at__gte=user.created_at)
        for i in message:
            message_id = i.id
            user_message = UserMessage.objects.filter(message=message_id, user=user.id)
            if len(user_message) == 0:
                usermessage = UserMessage()
                usermessage.user = user
                usermessage.message = i
                usermessage.save()

        coins = Coin.objects.filter(is_disabled=False)
        is_usermessage = UserMessage.objects.filter(user_id=user_id, message_id=12).count()
        if is_usermessage == 0:
            user_message = UserMessage()
            user_message.status = 0
            user_message.user = user
            user_message.message_id = 12
            user_message.save()

        for coin in coins:
            coin_pk = coin.id
            coin_initialization(user_id, coin_pk)

        give_info = CoinGive.objects.get(pk=1)  # 货币赠送活动
        end_date = give_info.end_time.strftime("%Y%m%d%H%M%S")
        today = date.today()
        today_time = today.strftime("%Y%m%d%H%M%S")
        if today_time < end_date and user.is_robot == 0:  # 活动期间
            is_give = CoinGiveRecords.objects.filter(user_id=user_id).count()
            if is_give == 0:
                user_coin = UserCoin.objects.filter(coin_id=give_info.coin_id, user_id=user_id).first()
                user_coin_give_records = CoinGiveRecords()
                user_coin_give_records.start_coin = user_coin.balance
                user_coin_give_records.user = user
                user_coin_give_records.coin_give = give_info
                user_coin_give_records.lock_coin = give_info.number
                user_coin_give_records.save()
                user_coin.balance += give_info.number
                user_coin.save()
                user_message = UserMessage()
                user_message.status = 0
                user_message.user = user
                user_message.message_id = 11
                user_message.save()
                coin_bankruptcy = CoinDetail()
                coin_bankruptcy.user = user
                coin_bankruptcy.coin_name = 'USDT'
                coin_bankruptcy.amount = '+' + str(give_info.number)
                coin_bankruptcy.rest = Decimal(user_coin.balance)
                coin_bankruptcy.sources = 4
                coin_bankruptcy.save()

        # usercoins = UserCoin.objects.get(user_id=user.id, coin__name="HAND")  # 破产赠送hand功能
        # record_number = Record.objects.filter(user_id=usercoins.user.id, roomquiz_id=1, type=0).count()
        # if int(usercoins.balance) < 1000 and int(roomquiz_id) == 1 and record_number < 1 and user.is_robot == 0:
        #     today = date.today()
        #     is_give = BankruptcyRecords.objects.filter(user_id=user_id, coin_name="HAND", money=10000,
        #                                                created_at__gte=today).count()
        #     if is_give <= 0:
        #         usercoins.balance += Decimal(10000)
        #         usercoins.save()
        #         coin_bankruptcy = CoinDetail()
        #         coin_bankruptcy.user = user
        #         coin_bankruptcy.coin_name = 'HAND'
        #         coin_bankruptcy.amount = '+' + str(10000)
        #         coin_bankruptcy.rest = Decimal(usercoins.balance)
        #         coin_bankruptcy.sources = 4
        #         coin_bankruptcy.save()
        #         bankruptcy_info = BankruptcyRecords()
        #         bankruptcy_info.user = user
        #         bankruptcy_info.coin_name = 'HAND'
        #         bankruptcy_info.money = Decimal(10000)
        #         bankruptcy_info.save()
        #         user_message = UserMessage()
        #         user_message.status = 0
        #         user_message.user = user
        #         user_message.message_id = 10  # 修改密码
        #         user_message.save()

        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        usercoin_avatar = usercoin.coin.icon
        user_coin = usercoin.balance
        recharge_address = usercoin.address

        user_invitation_number = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter_id=user.id,
                                                               is_effective=1).count()
        if user_invitation_number > 0:
            user_invitation_info = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter_id=user.id,
                                                                 is_effective=1)
            for a in user_invitation_info:
                try:
                    userbalance = UserCoin.objects.get(coin_id=a.coin, user_id=user.id)
                except Exception:
                    return 0
                # if int(a.coin) == 9:
                #     a.is_deleted = 1
                #     a.save()
                #     usdt_balance.balance += a.money
                #     usdt_balance.save()
                #     coin_detail = CoinDetail()
                #     coin_detail.user = user
                #     coin_detail.coin_name = 'USDT'
                #     coin_detail.amount = '+' + str(a.money)
                #     coin_detail.rest = usdt_balance.balance
                #     coin_detail.sources = 8
                #     coin_detail.save()
                #     usdt_give = CoinGiveRecords.objects.get(user_id=user.id)
                #     usdt_give.lock_coin += a.money
                #     usdt_give.save()
                # else:
                userbalance.balance += a.money
                userbalance.save()
                coin_detail = CoinDetail()
                coin_detail.user = user
                coin_detail.coin_name = userbalance.coin.name
                coin_detail.amount = '+' + str(a.money)
                coin_detail.rest = userbalance.balance
                coin_detail.sources = 8
                coin_detail.save()
                a.is_deleted = 1
                a.save()
                u_mes = UserMessage()  # 邀请注册成功后消息
                u_mes.status = 0
                u_mes.user = user
                if a.invitee_one != 0:
                    u_mes.message_id = 1  # 邀请t1消息
                else:
                    u_mes.message_id = 2  # 邀请t2消息
                u_mes.save()

        lr = LoginRecord()  # 登录记录
        lr.user = user
        lr.login_type = request.META.get('HTTP_X_API_KEY', '')
        lr.ip = request.META.get("REMOTE_ADDR", '')
        lr.save()

        is_message = message_hints(user_id)  # 是否有未读消息

        return self.response({'code': 0, 'data': {
            'user_id': items[0]["id"],
            'nickname': items[0]["nickname"],
            'avatar': items[0]["avatar"],
            'usercoin': normalize_fraction(user_coin, int(usercoin.coin.coin_accuracy)),
            'coin_name': coin_name,
            'usercoin_avatar': usercoin_avatar,
            'recharge_address': recharge_address,
            'integral': normalize_fraction(items[0]["integral"], 2),
            'area_code': items[0]["area_code"],
            'telephone': items[0]["telephone"],
            'is_passcode': items[0]["is_passcode"],
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

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        sql = "SELECT balance from users_usercoin where coin_id = 6 and user_id=" + str(user_id)
        user_coin = get_sql(sql)[0][0]  # 用户拥有的ETH
        my_ranking = {
            "user_id": user_id,
            "avatar": user.avatar,
            "nickname": user.nickname,
            "win_ratio": normalize_fraction(user_coin, 2),
            "ranking": "未上榜"
        }
        if 'page' not in request.GET:
            page = 1
        else:
            page = int(request.GET.get('page'))
        i = page * 10
        sql = "SELECT user_id,sum(balance) as aaa from users_usercoin where coin_id = 6 GROUP BY user_id ORDER BY aaa desc limit " + str(
            i - 10) + "," + str(i) + ";"
        lists = get_sql(sql)  # 用户拥有的ETH
        sql = "SELECT user_id,sum(balance) as aaa from users_usercoin where coin_id = 6 GROUP BY user_id ORDER BY aaa desc limit 100"
        user_lists = get_sql(sql)  # 用户拥有的ETH
        a = 1
        for i in user_lists:
            if int(i[0]) == int(user_id):
                my_ranking["ranking"] = a
            a += 1

        data = []
        s = (page - 1) * 10
        for list in lists:
            user_info = User.objects.get(id=int(list[0]))
            s = s + 1
            is_user = 0
            if int(user_id) == int(list[0]):
                is_user = 1
            data.append({
                'user_id': list[0],
                'avatar': user_info.avatar,
                'nickname': user_info.nickname,
                'is_user': is_user,
                'win_ratio': normalize_fraction(list[1], 2),
                'ranking': s,
            })

        return self.response({'code': 0, 'data': {'my_ranking': my_ranking, 'list': data, }})

    # serializer_class = UserInfoSerializer
    #
    # def get_queryset(self):
    #     return User.objects.all().order_by('-integral', 'id')[:100]
    #
    # def list(self, request, *args, **kwargs):
    #     results = super().list(request, *args, **kwargs)
    #     Progress = results.data.get('results')
    #     user = request.user
    #     user_gsg = UserCoin.objects.get(user_id=user.id, coin_id=6)
    #     user_arr = User.objects.all().values_list('id').order_by('-integral', 'id')[:100]
    #     my_ran = "未上榜"
    #     if self.request.GET.get('language') == 'en':
    #         my_ran = "Not on the list"
    #     index = 0
    #     for i in user_arr:
    #         index = index + 1
    #         if i[0] == user.id:
    #             my_ran = index
    #     avatar = user.avatar
    #     nickname = user.nickname
    #     integral = user_gsg.balance
    #     print("integral=========================", integral)
    #     # win_ratio = user.victory
    #     # if user.victory == 0:
    #     #     win_ratio = 0
    #     # usercoin = UserCoin.objects.get(user_id=user.id, coin_id=1)
    #     my_ranking = {
    #         "user_id": user.id,
    #         "avatar": avatar,
    #         "nickname": nickname,
    #         "win_ratio": normalize_fraction(integral, 2),
    #         "ranking": my_ran
    #     }
    #     list = []
    #     if 'page' not in request.GET:
    #         page = 1
    #     else:
    #         page = int(request.GET.get('page'))
    #     i = (page - 1) * 10
    #     for fav in Progress:
    #         i = i + 1
    #         user_id = fav.get('id')
    #         integral = fav.get('integral')
    #         list.append({
    #             'user_id': user_id,
    #             'avatar': fav.get('avatar'),
    #             'nickname': fav.get('nickname'),
    #             'is_user': fav.get('is_user'),
    #             'win_ratio': normalize_fraction(integral, 2),
    #             'ranking': i,
    #         })
    #         list.sort(key=lambda x: x["ranking"])
    #
    #     return self.response({'code': 0, 'data': {'my_ranking': my_ranking, 'list': list, }})


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
        user_id = request.user.id
        is_sign = sign_confirmation(user_id)  # 是否签到
        data = []
        for list in items:
            data.append({
                "id": list["id"],
                "days": list["days"],
                "icon": list["icon"],
                "name": list["name"],
                "rewards": list["rewards"],
                "is_sign": list["is_sign"],
                "is_selected": list["is_selected"]
            })
        return self.response({'code': 0, 'data': data, 'sign': is_sign})


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
            daily = DailyLog()
            sign_date = str(0)

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
        # date_last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # end_date = "2018-06-24 00:00:00"
        # if date_last > end_date:
        try:
            dailysettings = DailySettings.objects.get(days=fate)
        except DailySettings.DoesNotExist:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        rewards = dailysettings.rewards
        user_coin = UserCoin.objects.get(user_id=user_id, coin_id=dailysettings.coin.id)
        user_coin.balance += Decimal(rewards)
        user_coin.save()
        daily.sign_date = time.strftime('%Y-%m-%d %H:%M:%S')
        daily.user_id = user_id
        daily.save()
        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = dailysettings.coin.name
        coin_detail.amount = '+' + str(rewards)
        coin_detail.rest = Decimal(user_coin.balance)
        coin_detail.sources = 7
        coin_detail.save()

        content = {'code': 0,
                   'data': normalize_fraction(rewards, 2),
                   'icon': dailysettings.coin.icon,
                   'name': dailysettings.coin.name
                   }
        # else:
        #     if fate == 1:
        #         rewards = 6
        #     if fate == 2:
        #         rewards = 8
        #     if fate == 3:
        #         rewards = 10
        #     if fate == 4:
        #         rewards = 12
        #     if fate == 5:
        #         rewards = 14
        #     if fate == 6:
        #         rewards = 16
        #     if fate == 7:
        #         rewards = 18
        #     user.integral += rewards
        #     user.save()
        #     daily.sign_date = time.strftime('%Y-%m-%d %H:%M:%S')
        #     daily.user_id = user_id
        #     daily.save()
        #     coin_detail = CoinDetail()
        #     coin_detail.user = user
        #     coin_detail.coin_name = 'GSG'
        #     coin_detail.amount = '+' + str(rewards)
        #     coin_detail.rest = Decimal(user.integral)
        #     coin_detail.sources = 7
        #     coin_detail.save()
        #
        #     content = {'code': 0,
        #                'data': normalize_fraction(rewards, 2),
        #                'icon': '',
        #                'name': ''
        #                }

        return self.response(content)


class MessageListView(ListAPIView, DestroyAPIView):
    """
    通知列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = MessageListSerialize

    def get_queryset(self):
        user = self.request.user.id
        type = self.request.parser_context['kwargs']['type']
        list = ""
        if int(type) == 1:
            list = UserMessage.objects.filter(Q(user_id=user), Q(message__type=1),
                                              Q(status=1) | Q(status=0)).order_by("status", "-created_at")
        elif int(type) == 2:
            list = UserMessage.objects.filter(Q(user_id=user), Q(message__type=2) | Q(message__type=3),
                                              Q(status=1) | Q(status=0)).order_by("status", "-created_at")
        return list

    def list(self, request, *args, **kwargs):
        user = self.request.user.id
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        public_sign = 0
        if message_sign(user, 2) or message_sign(user, 3):
            public_sign = 1
        system_sign = message_sign(user, 1)
        for list in items:
            data.append({
                "user_message_id": list["id"],
                "message_id": list["message"],
                'type': list["type"],
                'message_title': list["titles"],
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
        user = self.request.user.id
        user_message_id = kwargs['user_message_id']
        try:
            user_message = UserMessage.objects.get(pk=user_message_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_message.status = 1
        user_message.save()
        public_sign = 0
        if message_sign(user, 2) or message_sign(user, 3):
            public_sign = 1
        system_sign = message_sign(user, 1)
        if int(user_message.message.type) == 3:
            data = user_message.content
            if self.request.GET.get('language') == 'en':
                data = user_message.content_en
                if data == '' or data == None:
                    data = user_message.content
            content = {'code': 0,
                       'data': data,
                       'status': user_message.status,
                       'system_sign': system_sign,
                       'public_sign': public_sign
                       }
        else:
            data = user_message.message.content
            if self.request.GET.get('language') == 'en':
                data = user_message.message.content_en
                if data == '' or data == None:
                    data = user_message.message.content
            content = {'code': 0,
                       'data': data,
                       'status': user_message.status,
                       'system_sign': system_sign,
                       'public_sign': public_sign
                       }
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
        list = UserCoin.objects.filter(user_id=user).order_by('coin__coin_order')
        return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        user_info = request.user
        Progress = results.data.get('results')
        data = []
        try:
            # user_info = User.objects.get(id=user)
            eth = UserCoin.objects.get(user_id=user_info.id, coin__name='ETH')
            user_gsg = UserCoin.objects.get(user_id=user_info.id, coin_id=6)
        except Exception:
            raise

        for list in Progress:
            temp_dict = {
                'coin_order': list["coin_order"],
                'icon': list["icon"],
                'coin_name': list["coin_name"],
                'coin': list["coin"],
                'recharge_address': list["address"],
                'balance': list["balance"],
                'locked_coin': list["locked_coin"],
                'is_reality': list["is_reality"],
                'is_recharge': list["is_recharge"],
                'service_charge': list["service_charge"],
                'service_coin': list["service_coin"],
                'min_present': list["min_present"],
                'recent_address': list["recent_address"]
            }
            if temp_dict['coin_name'] == 'HAND':
                temp_dict['eth_balance'] = normalize_fraction(eth.balance, eth.coin.coin_accuracy)
                temp_dict['eth_address'] = eth.address
                temp_dict['eth_coin_id'] = eth.coin_id
            if temp_dict['coin_name'] == 'GSG':
                coinlocks = CoinLock.objects.filter(coin__name='GSG').order_by('period')
                if not coinlocks.exists():
                    raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
                else:
                    for i, x in enumerate(coinlocks):
                        s = 'day_' + str(i)
                        temp_dict[s] = x.period
                temp_dict['is_lock_valid'] = list['is_lock_valid']
            data.append(temp_dict)

        return self.response({'code': 0, 'user_name': user_info.nickname, 'user_avatar': user_info.avatar,
                              'user_integral': normalize_fraction(user_gsg.balance, 2), 'data': data})


class AssetLock(CreateAPIView):
    """
    GSG锁定
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'locked_days', 'amounts')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        userid = self.request.user.id
        try:
            userinfo = User.objects.get(id=userid)
        except Exception:
            raise
        amounts = Decimal(str(request.data.get('amounts')))
        locked_days = int(request.data.get('locked_days'))
        # coin_id = int(request.data.get('coin_id'))
        coin_id = 6
        try:
            coin = Coin.objects.get(id=coin_id)
            user_coin = UserCoin.objects.select_for_update().get(user_id=userid, coin_id=coin_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        coin_configs = CoinLock.objects.filter(period=locked_days, is_delete=0, coin_id=coin.id)
        if not coin_configs.exists():
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if amounts <= 0 or amounts > user_coin.balance:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_coin.balance -= amounts
        user_coin.save()
        ulcoin = UserCoinLock()
        ulcoin.user = userinfo
        ulcoin.amount = amounts
        ulcoin.coin_lock = coin_configs[0]
        ulcoin.save()
        ulcoin.end_time = ulcoin.created_at + timedelta(days=locked_days)
        ulcoin.save()
        coin_detail = CoinDetail()
        coin_detail.user = userinfo
        coin_detail.coin_name = user_coin.coin.name
        coin_detail.amount = '-' + str(amounts)
        coin_detail.rest = user_coin.balance
        coin_detail.sources = CoinDetail.LOCK
        coin_detail.save()
        content = {'code': 0}
        return self.response(content)


class UserPresentationView(CreateAPIView):
    """
    币种提现
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'p_address', 'p_address_name', 'code', 'password', 'p_amount', 'c_id')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        userid = self.request.user.id
        try:
            userinfo = User.objects.get(pk=userid)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        password = request.data.get('password')
        if not userinfo.check_password(password):
            raise ParamErrorException(error_code.API_70108_USER_PRESENT_PASSWORD_ERROR)
        code = request.data.get('code')
        sms = Sms.objects.filter(telephone=userinfo.telephone, type=6).order_by('-id').first()
        if (sms is None) or (sms.code != code):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})
        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.now().timetuple())
        if current_time - time.mktime(sent_time.timetuple()) >= settings.SMS_CODE_EXPIRE_TIME:
            return self.response({'code': error_code.API_20403_SMS_CODE_EXPIRE})
        p_address = request.data.get('p_address')
        p_address_name = request.data.get('p_address_name')
        c_id = request.data.get('c_id')
        if int(c_id) == 6:
            return self.response({'code': error_code.API_70109_USER_PRESENT_ADDRESS_ERROR})

        try:
            coin = Coin.objects.get(id=int(c_id))
            user_coin = UserCoin.objects.select_for_update().get(user_id=userid, coin_id=coin.id)
        except Exception:
            raise
        p_amount = eval(request.data.get('p_amount'))

        try:
            coin_out = CoinOutServiceCharge.objects.get(coin_out=coin.id)
        except Exception:
            raise
        # if coin.name == 'USDT':
        #     records = Record.objects.filter(source=Record.GIVE, user_id=userid, roomquiz_id=6).values(
        #         'quiz_id').distinct().count()
        #     if records < 6:
        #         raise ParamErrorException(error_code.API_70109_USER_PRESENT_USDT_QUIZ_LT_6)

        if coin.name != 'HAND' and coin.name != 'USDT':
            if user_coin.balance < coin_out.value:
                raise ParamErrorException(error_code.API_70107_USER_PRESENT_BALANCE_NOT_ENOUGH)

        elif coin.name == 'USDT':  # usdt
            try:
                coin_give = CoinGiveRecords.objects.get(user_id=userid)
            except Exception:
                raise
            balance = user_coin.balance - Decimal(str(coin_give.lock_coin))
            if balance < coin_out.value:
                raise ParamErrorException(error_code.API_70107_USER_PRESENT_BALANCE_NOT_ENOUGH)
        else:
            try:
                coin_eth = UserCoin.objects.get(user_id=userid, coin_id=coin_out.coin_payment)
            except Exception:
                raise
            if coin_eth.balance < coin_out.value:
                raise ParamErrorException(error_code.API_70107_USER_PRESENT_BALANCE_NOT_ENOUGH)
        if p_amount > user_coin.balance or p_amount <= 0 or p_amount < coin.cash_control:
            if p_amount > user_coin.balance:

                if coin.name == "USDT":  # usdt
                    try:
                        coin_give = CoinGiveRecords.objects.get(user_id=userid)
                    except Exception:
                        raise
                    balance = user_coin.balance - Decimal(str(coin_give.lock_coin))
                    if p_amount > balance:
                        raise ParamErrorException(error_code.API_70101_USER_PRESENT_AMOUNT_GT)

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

        if coin.name == 'ETH' or coin.name == 'HAND' or coin.name == 'INT':
            if not p_address.startswith('0'):
                raise ParamErrorException(error_code.API_70109_USER_PRESENT_ADDRESS_ERROR)

        if coin.name == 'BTC' or coin.name == 'USDT':
            if not p_address.startswith('1') and not p_address.startswith('3'):
                raise ParamErrorException(error_code.API_70109_USER_PRESENT_ADDRESS_ERROR)

        if p_address_name == '':
            raise ParamErrorException(error_code.API_70106_USER_PRESENT_ADDRESS_NAME)

        if coin.name != 'HAND':
            user_coin.balance = user_coin.balance - Decimal(str(p_amount))
        else:
            user_coin.balance -= Decimal(str(p_amount))
            if coin_eth.balance >= coin_out.value:
                coin_eth.balance -= coin_out.value
                coin_eth.save()
        user_coin.save()
        presentation = UserPresentation()
        presentation.user = userinfo
        presentation.coin = coin
        if coin.name == 'HAND':
            presentation.amount = Decimal(str(p_amount))
        else:
            presentation.amount = Decimal(str(p_amount)) - coin_out.value
        try:
            presentation.rest = user_coin.balance
        except Exception:
            raise
        presentation.address = p_address
        presentation.address_name = p_address_name
        presentation.save()
        coin_detail = CoinDetail()
        coin_detail.user = userinfo
        coin_detail.coin_name = coin.name
        if coin.name == 'HAND':
            coin_detail.amount = Decimal(str(p_amount))
        else:
            coin_detail.amount = Decimal(str(p_amount)) - coin_out.value
        coin_detail.rest = Decimal(user_coin.balance)
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
        query = UserPresentation.objects.filter(user_id=userid, coin_id=c_id)
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for x in items:
            data.append(
                {
                    'id': x['id'],
                    'coin_id': x['coin_id'],
                    'coin_icon': x['coin_icon'],
                    'amount': normalize_fraction(x['amount'], 8),
                    'address': x['address'],
                    'status_code': x['status'],
                    'created_at': x['created_at']
                }
            )
        return self.response({'code': 0, 'data': data})


class PresentationDetailView(RetrieveAPIView):
    """
    提现记录表明细
    """
    permission_classes = (LoginRequired,)

    def retrieve(self, request, *args, **kwargs):
        language = request.GET.get('language')
        rc_id = int(kwargs['p_id'])
        try:
            record = UserPresentation.objects.get(id=rc_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            service = CoinOutServiceCharge.objects.get(coin_out_id=record.coin_id)
        except Exception:
            raise
        sers = PresentationSerialize(record).data
        data = {
            'id': sers['id'],
            'coin_icon': sers['coin_icon'],
            'amount': normalize_fraction(sers['amount'], 8),
            'service_value': normalize_fraction(service.value, 5),
            'service_coin_name': service.coin_payment.name,
            'address_name': sers['address_name'],
            'address': sers['address'],
            'created_at': sers['created_at']
        }
        status = int(sers['status'])
        data['status_code'] = status
        if status == 0:
            if language == 'en':
                data['status'] = 'Processing'
                data['text'] = 'Processing...'
            else:
                data['status'] = '提现申请中'
                data['text'] = '提现申请中...'

        elif status == 1:
            if language == 'en':
                data['status'] = 'Success'
            else:
                data['status'] = '提现成功'
            data['text'] = 'Txhash:' + sers['txid']
        else:
            if language == 'en':
                data['status'] = 'Fail'
                data['text'] = 'Reject:' + sers['feedback']
            else:
                data['status'] = '提现失败'
                data['text'] = '拒绝理由：' + sers['feedback']
        return self.response({'code': 0, 'data': data})


class RechargeListView(ListAPIView):
    """
    充值记录表
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserRechargeSerizlize

    def get_queryset(self):
        user = self.request.user.id
        coin_id = self.kwargs['coin_id']
        recharges = UserRecharge.objects.filter(user_id=user, coin_id=coin_id, is_deleted=0)
        return recharges

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for x in items:
            data.append(
                {
                    'id': x['id'],
                    'coin_id': x['coin_id'],
                    'coin_icon': x['coin_icon'],
                    'amount': normalize_fraction(x['amount'], 8),
                    'address': x['address'],
                    'status': x['status'],
                    'trade_at': x['trade_at']
                }
            )
        return self.response({'code': 0, 'data': data})


class RechargeDetailView(RetrieveAPIView):
    """
    充值记录明细
    """
    permission_classes = (LoginRequired,)

    def retrieve(self, request, *args, **kwargs):
        r_id = int(kwargs['r_id'])
        try:
            record = UserRecharge.objects.get(id=r_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        sers = UserRechargeSerizlize(record).data
        data = {
            'id': sers['id'],
            'coin_id': sers['coin_id'],
            'coin_icon': sers['coin_icon'],
            'amount': normalize_fraction(sers['amount'], 8),
            'address_name': sers['address'],
            'address': sers['address'],
            'status': sers['status'],
            'trade_at': sers['trade_at']
        }
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

class LockListView(ListAPIView):
    """
    锁定记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = LockSerialize

    def get_queryset(self):
        userid = self.request.user.id
        query = UserCoinLock.objects.filter(user_id=userid).order_by('-created_at')
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for x in items:
            # if x['end_time'] >= x['created_at']:
            data.append(
                {
                    "id": x['id'],
                    "amount": x['amount'],
                    "period": x['period'],
                    "icon": x['icon'],
                    "created_at": x['created_at'],
                    "is_free": 1 if x['is_free'] else 0,
                    "status": x['status']
                }
            )
        return self.response({'code': 0, 'data': data})


class LockDetailView(RetrieveUpdateAPIView):
    """
    锁定记录
    """
    permission_classes = (LoginRequired,)

    def retrieve(self, request, *args, **kwargs):
        id = kwargs['id']
        try:
            coin_lock = UserCoinLock.objects.get(id=id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        sers = LockSerialize(coin_lock).data
        data = {
            "status": sers['status'],
            "period": sers['period'],
            "amount": sers['amount'],
            "created_at": sers['created_at']
        }
        divided = Dividend.objects.filter(user_lock_id=coin_lock.id).values('coin__name', 'coin__icon').annotate(
            Sum('divide')).order_by('coin_id')
        dividend = []
        if divided.exists():
            for x in divided:
                dividend.append(
                    {
                        "coin_name": x['coin__name'],
                        "coin_icon": x['coin__icon'],
                        "divide": normalize_fraction(x['divide__sum'], 8)
                    }
                )
        data["dividend"] = dividend
        return self.response({'code': 0, 'data': data})

    def put(self, request, *args, **kwargs):
        id = int(kwargs['id'])
        days_extra = int(request.data.get('days_extra'))
        if not isinstance(days_extra, int):
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            user_lock = UserCoinLock.objects.get(id=id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_lock.end_time += timedelta(days_extra)
        user_lock.save()
        return self.response({'code': 0})


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
        except data.DoesNotExist:
            raise
        if index == 1:
            return self.response({'code': 0, 'data': data.about})
        elif index == 2:
            return self.response({'code': 0, 'data': data.helps})
        elif index == 3:
            return self.response({'code': 0, 'data': data.sv_contractus})
        else:
            return self.response({'code': 0, 'data': data.sv_contractus})


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

    def post(self, request):
        value = value_judge(request, "password", "code", "username")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if 'area_code' not in request.data:
            area_code = 86
        else:
            area_code = request.data.get('area_code')
        password = request.data.get('password')
        username = request.data.get('username')
        try:
            userinfo = User.objects.get(area_code=area_code, username=username)
        except Exception:
            raise ParamErrorException(error_code.API_20103_TELEPHONE_UNREGISTER)

        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(area_code=area_code, telephone=userinfo.telephone).order_by('-id').first()
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

        # u_mes = UserMessage()  # 修改密码后消息
        # u_mes.status = 0
        # u_mes.user = userinfo
        # u_mes.message_id = 7  # 修改密码
        # u_mes.save()

        content = {'code': 0}
        return self.response(content)


# class UserRechargeView(ListCreateAPIView):
#     """
#     用户充值
#     """
#     permission_classes = (LoginRequired,)
#
#     def post(self, request, *args, **kwargs):
#         index = kwargs.get('index')
#         if 'recharge' not in request.data or 'r_address' not in request.data:
#             raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
#         r_address = request.data.get('r_address')
#         if not r_address:
#             raise ParamErrorException(error_code.API_70201_USER_RECHARGE_ADDRESS)
#         uuid = request.user.id
#         try:
#             user_coin = UserCoin.objects.get(id=index, user_id=uuid)
#         except Exception:
#             raise
#         recharge = Decimal(request.data.get('recharge'))
#         if recharge <= 0:
#             raise ParamErrorException(error_code.API_70202_USER_RECHARGE_AMOUNT)
#         user_coin.balance += recharge
#         user_coin.save()
#         form_recharge = UserRecharge.objects.filter(user_id=uuid)
#         if not form_recharge.exists():  # 活动送Hand币,活动时间在2018年6月1日-2018年7月13日
#             start_time = time.mktime(datetime.strptime('2018-06-01 00:00:00', '%Y-%m-%d %H:%M:%S').timetuple())
#             end_time = time.mktime(datetime.strptime('2018-07-14 00:00:00', '%Y-%m-%d %H:%M:%S').timetuple())
#             now_time = time.mktime(datetime.now().timetuple())
#             if now_time >= start_time and now_time <= end_time:
#                 try:
#                     user_reward = UserCoin.objects.get(user_id=uuid, coin__name='HAND')
#                 except Exception:
#                     raise
#                 user_reward.balance += Decimal('2888')
#                 user_reward.save()
#                 reward_detail = CoinDetail(user_id=uuid, coin_name=user_reward.coin.name, amount='2888',
#                                            rest=user_reward.balance, sources=4)
#                 reward_detail.save()
#                 u_ms = UserMessage()  # 活动消息通知
#                 u_ms.status = 0
#                 u_ms.user_id = uuid
#                 u_ms.message_id = 3  # 消息3 充值活动奖励情况
#                 u_ms.save()
#         user_recharge = UserRecharge(user_id=uuid, coin_id=index, amount=recharge, address=r_address)
#         user_recharge.save()
#         coin_detail = CoinDetail(user_id=uuid, coin_name=user_coin.coin.name, amount=str(recharge),
#                                  rest=user_coin.balance, sources=1)
#         coin_detail.save()
#         return self.response({'code': 0})


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
            raise
        uuid = self.request.user.id
        query_s = CoinDetail.objects.filter(user_id=uuid, sources__in=[1, 2], coin_name=coin.name).order_by(
            '-created_at')
        return query_s

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        language = request.GET.get('language', '')
        temp_dict = {}
        for x in items:
            if language == 'en':
                x['month'] = datetime.strptime(x['month'], '%Y年%m月').strftime('%m/%Y')
                if x['status'] == '提现申请中':
                    x['status'] = 'Processing'
                if x['status'] == '提现成功' or x['status'] == '充值成功':
                    x['status'] = 'Success'
                if x['status'] == '提现失败':
                    x['status'] = 'Fail'
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
        language = request.GET.get('language', '')
        try:
            coin = Coin.objects.get(id=self.kwargs['coin'])
            item = CoinDetail.objects.get(id=pk, coin_name=coin.name)
        except Exception:
            raise
        serialize = CoinOperateSerializer(item)
        data = serialize.data
        if language == 'en':
            data['month'] = datetime.strptime(data['month'], '%Y年%m月').strftime('%m/%Y')
            if data['status'] == '提现申请中':
                data['status'] = 'Processing'
            if data['status'] == '提现成功' or data['status'] == '充值成功':
                data['status'] = 'Success'
            if data['status'] == '提现失败':
                data['status'] = 'Fail'
        return self.response({'code': 0, 'data': data})


class VersionUpdateView(RetrieveAPIView):
    """
    版本更新
    """

    def retrieve(self, request, *args, **kwargs):
        version = request.query_params.get('version')
        mobile_type = request.META.get('HTTP_X_API_KEY')
        language = request.GET.get('language')
        if str(mobile_type).upper() == "ANDROID":
            type = 0
        if str(mobile_type).upper() == "IOS" or str(mobile_type).upper() == "HTML5":  # 由于目前ios版本是内嵌html5的网页
            type = 1
        versions = AndroidVersion.objects.filter(is_delete=0, mobile_type=type)
        if not versions.exists():
            return self.response({'code': 0, 'is_new': 0})
        else:
            last_version = versions.order_by('-create_at')[0]
        if last_version.version == version:
            return self.response({'code': 0, 'is_new': 0})
        else:
            serialize = AndroidSerializer(last_version)
            if type == 1:
                data = serialize.data
                ul_url = data['upload_url'].rsplit('/', 1)[0] + '/version_%s_IOS.plist' % last_version.version
                data['upload_url'] = ul_url
            else:
                data = serialize.data
                data['is_update'] = True if data['is_update'] else False
                data['is_delete'] = True if data['is_delete'] else False
            if language == 'en':
                data['comment'] = data['comment_en']
            return self.response({'code': 0, 'is_new': 1, 'data': data})


class ImageUpdateView(CreateAPIView):
    """
    更换上传头像
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        form = ImageForm(request.POST, request.FILES)
        safe_image_type = request.FILES['image'].name.strip().split('.')[-1] in ('jpg', 'png', 'jpeg')
        if safe_image_type:
            if form.is_valid():
                new_doc = Im(image=request.FILES['image'])
                new_doc.save()
                temp_img = new_doc
            else:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        else:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if not temp_img:
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

    def get_name_avatar(self):
        """
        获取已经下载的用户昵称和头像
        :return:
        """
        key_name_avatar = 'new_avatar_key'

        line_number = get_cache(key_name_avatar)
        if line_number is None:
            line_number = 1

        file_avatar_nickname = settings.CACHE_DIR + '/new_avatar.lst'
        avatar_nickname = linecache.getline(file_avatar_nickname, line_number)
        a = avatar_nickname.split('_')
        if len(a) > 2:
            folder = str(a[0])
            suffix = str(a[1]) + "_" + str(a[2])
        else:
            folder, suffix = avatar_nickname.split('_')

        avatar_url = settings.MEDIA_DOMAIN_HOST + "/avatar/" + folder + '/' + avatar_nickname

        line_number += 1
        set_cache(key_name_avatar, line_number)
        myfile = open(file_avatar_nickname)
        lines = len(myfile.readlines())
        if line_number >= lines:
            delete_cache(key_name_avatar)
        return avatar_url

    def post(self, request, *args, **kwargs):
        source = request.META.get('HTTP_X_API_KEY')
        invitation_id = request.data.get('invitation_id')
        telephone = request.data.get('telephone')
        code = request.data.get('code')
        area_code = request.data.get('area_code')
        password = request.data.get('password')
        device_token = ""
        if 'device_token' in request.data:
            device_token = request.data.get('device_token')

        # 图形验证码，目前只限于HTML5 - 登录请求
        captcha_valid_code = User.objects.captcha_valid(request)
        if captcha_valid_code > 0:
            raise ParamErrorException(captcha_valid_code)
            # return self.response({'code': captcha_valid_code})

        # 校验手机短信验证码
        message = Sms.objects.filter(telephone=telephone, code=code, type=Sms.REGISTER)
        if len(message) == 0:
            return self.response({
                'code': error_code.API_20402_INVALID_SMS_CODE
            })
        ip_address = request.META.get("REMOTE_ADDR", '')
        # 判断同一IP地址是否重复注册
        # ip1, ip2, ip3, ip4 = ip_address.split('.')
        # startswith = ip1 + '.' + ip2 + '.' + ip3 + '.'
        # ip_users = User.objects.filter(ip_address__startswith=startswith).count()
        # if ip_users > 2:
        #     raise ParamErrorException(error_code.API_20404_SAME_IP_ERROR)

        # 判断该手机号码是否已经注册
        user = User.objects.filter(username=telephone)
        if len(user) > 0:
            return self.response({
                'code': error_code.API_20102_TELEPHONE_REGISTERED
            })
        all_money = UserInvitation.objects.filter(coin=4, is_deleted=1).aggregate(Sum('money'))
        all_money = all_money['money__sum']  # 获得总钱数
        if all_money is not None:
            all_money += 2000
            if all_money > 200000000:
                raise ParamErrorException(error_code.API_60101_USER_INVITATION_MONEY)

        # 用户注册
        ur = UserRegister()
        avatar = self.get_name_avatar()
        nickname = str(telephone[0:3]) + "***" + str(telephone[7:])
        token = ur.register(source=source, username=telephone, password=password, area_code=area_code, avatar=avatar,
                            nickname=nickname, ip_address=ip_address, device_token=device_token)
        invitee_one = UserInvitation.objects.filter(invitee_one=int(invitation_id)).count()
        try:
            user = ur.get_user(telephone)
            user_info = User.objects.get(pk=user.id)
        except DailyLog.DoesNotExist:
            return 0

        if invitee_one > 0:  # 邀请人为他人T1.
            try:
                invitee = UserInvitation.objects.filter(invitee_one=int(invitation_id)).first()
            except DailyLog.DoesNotExist:
                return 0
            on_line = invitee.inviter
            invitee_number = UserInvitation.objects.filter(inviter_id=on_line.id, coin=4, is_effective=1).count()
            try:
                is_robot = User.objects.get(pk=on_line.id)
            except DailyLog.DoesNotExist:
                return 0
            user_on_line = UserInvitation()  # 邀请T2是否已达上限
            if invitee_number < 10 and is_robot.is_robot == False:
                user_on_line.is_effective = 1
                user_on_line.money = 2000
                user_on_line.is_robot = False
            user_on_line.inviter = on_line
            user_on_line.invitee_two = user_info.id
            user_on_line.save()

        inviter_number = UserInvitation.objects.filter(inviter_id=int(invitation_id), coin=9).count()
        try:
            invitation = User.objects.get(pk=invitation_id)
        except DailyLog.DoesNotExist:
            return 0
        try:
            is_robot = User.objects.get(pk=invitation_id)
        except DailyLog.DoesNotExist:
            return 0
        give_info = CoinGive.objects.get(pk=1)  # 货币赠送活动
        end_date = give_info.end_time.strftime("%Y%m%d%H%M%S")
        today = date.today()
        today_time = today.strftime("%Y%m%d%H%M%S")
        user_go_line = UserInvitation()  # 邀请T1是否已达上限
        if inviter_number < 5 and today_time < end_date and is_robot.is_robot == False:
            user_go_line.is_effective = 1
            user_go_line.money = 3888
            # user_go_line.coin = 4
            user_go_line.is_robot = False
        user_go_line.inviter = invitation
        user_go_line.invitee_one = user_info.id
        user_go_line.save()

        if int(invitation.pk) == 2638:  # INT邀请活动
            invitation_number = IntInvitation.objects.filter(is_block=0).count()
            int_invitation = IntInvitation()
            int_invitation.invitee = user_info.id
            int_invitation.inviter = invitation
            int_invitation.coin = 1
            int_invitation.invitation_code = invitation.invitation_code
            if invitation_number >= 2000:
                int_invitation.money = 0
                int_invitation.is_deleted = False
            int_invitation.save()
            user_message = UserMessage()
            user_message.status = 0
            user_message.user = user_info
            user_message.message_id = 13
            user_message.save()
            if int_invitation.money > 0:
                int_user_coin = UserCoin.objects.get(user_id=user_info.pk, coin_id=1)
                int_user_coin.balance += Decimal(int_invitation.money)
                int_user_coin.save()
                coin_bankruptcy = CoinDetail()
                coin_bankruptcy.user = user_info
                coin_bankruptcy.coin_name = 'INT'
                coin_bankruptcy.amount = '+' + str(int_invitation.money)
                coin_bankruptcy.rest = Decimal(int_user_coin.balance)
                coin_bankruptcy.sources = 4
                coin_bankruptcy.save()

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
        user = self.request.user
        user_invitation_number = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter_id=user.id,
                                                               is_effective=1).count()
        if user_invitation_number > 0:
            user_invitation_info = UserInvitation.objects.filter(money__gt=0, is_deleted=0, inviter_id=user.id,
                                                                 is_effective=1)
            for a in user_invitation_info:
                try:
                    userbalance = UserCoin.objects.get(coin_id=a.coin, user_id=user.id)
                except Exception:
                    return 0
                # if int(a.coin) == 9:
                #     usdt_balance.balance += a.money
                #     usdt_balance.save()
                #     coin_detail = CoinDetail()
                #     coin_detail.user = user
                #     coin_detail.coin_name = 'USDT'
                #     coin_detail.amount = '+' + str(a.money)
                #     coin_detail.rest = usdt_balance.balance
                #     coin_detail.sources = 8
                #     coin_detail.save()
                #     try:
                #         usdt_give = CoinGiveRecords.objects.get(user_id=user.id)
                #     except Exception:
                #         return 0
                #     usdt_give.lock_coin += a.money
                #     usdt_give.save()
                # else:
                userbalance.balance += a.money
                userbalance.save()
                coin_detail = CoinDetail()
                coin_detail.user = user
                coin_detail.coin_name = userbalance.coin.name
                coin_detail.amount = '+' + str(a.money)
                coin_detail.rest = userbalance.balance
                coin_detail.sources = 8
                coin_detail.save()
                a.is_deleted = 1
                a.save()
                u_mes = UserMessage()  # 邀请注册成功后消息
                u_mes.status = 0
                u_mes.user = user
                if a.invitee_one != 0:
                    u_mes.message_id = 1  # 邀请t1消息
                else:
                    u_mes.message_id = 2  # 邀请t2消息
                u_mes.save()

        if user.invitation_code == '':
            invitation_code = random_invitation_code()
            user.invitation_code = invitation_code
            user.save()
        else:
            invitation_code = user.invitation_code
        invitation_number = UserInvitation.objects.filter(inviter=user.id).count()  # 总人数
        user_invitation_two = UserInvitation.objects.filter(invitee_one=0, inviter=user.id, is_deleted=1,
                                                            coin=4).aggregate(
            Sum('money'))
        user_invitation_one = UserInvitation.objects.filter(invitee_two=0, inviter=user.id, is_deleted=1,
                                                            coin=9).aggregate(
            Sum('money'))
        user_invitation_twos = user_invitation_two['money__sum']  # T2获得总钱数
        if user_invitation_twos == None:
            user_invitation_twos = 0
        user_invitation_ones = user_invitation_one['money__sum']  # T2获得总钱数
        if user_invitation_ones == None:
            user_invitation_ones = 0
        invitee_number = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=int(user.id), is_effective=1).count()
        invitee_number = 5 - int(invitee_number)
        if invitee_number < 0:
            invitee_number = 0
        return self.response(
            {'code': 0, 'user_invitation_number': invitation_number, 'one_moneys': user_invitation_ones,
             'moneys': user_invitation_twos,
             'invitation_code': invitation_code, 'invitee_number': invitee_number})


class InvitationUserView(ListAPIView):
    """
    扫描二维码拿用户消息
    """

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user_id = request.GET.get('from_id')
        try:
            user_info = User.objects.get(pk=user_id)
        except DailyLog.DoesNotExist:
            return 0

        invitation_code = user_info.invitation_code
        pk = user_info.pk
        nickname = user_info.nickname
        avatar = user_info.avatar
        username = user_info.username
        return self.response({'code': 0, "pk": pk, "nickname": nickname, "avatar": avatar, "username": username,
                              "invitation_code": invitation_code})


class InvitationMergeView(ListAPIView):
    """
    生成用户推广页面
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user

        sub_path = str(user.id % 10000)

        spread_path = settings.MEDIA_ROOT + 'spread/'
        if not os.path.exists(spread_path):
            os.mkdir(spread_path)

        save_path = spread_path + sub_path
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        if user.invitation_code == '':
            invitation_code = random_invitation_code()
            user.invitation_code = invitation_code
            user.save()
        else:
            invitation_code = user.invitation_code

        if self.request.GET.get('language') == 'en':
            if os.access(save_path + '/qrcode_' + str(user.id) + '_new_en.jpg', os.F_OK):
                base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_en.jpg'
                qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
                return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data})
        else:
            if os.access(save_path + '/qrcode_' + str(user.id) + '_new.jpg', os.F_OK):
                base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new.jpg'
                qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
                return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data})

        pygame.init()
        # 设置字体和字号
        font = pygame.font.SysFont('Microsoft YaHei', 64)
        # 渲染图片，设置背景颜色和字体样式,前面的颜色是字体颜色
        ftext = font.render(invitation_code, True, (255, 255, 255), (116, 68, 11))
        # 保存图片
        invitation_code_address = save_path + '/invitation_code_' + str(user.id) + '.jpg'
        pygame.image.save(ftext, invitation_code_address)  # 图片保存地址
        # qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)

        if self.request.GET.get('language') == 'en':
            base_img = Image.open(settings.BASE_DIR + '/uploads/fx_bk_en.jpg')
        else:
            base_img = Image.open(settings.BASE_DIR + '/uploads/fx_bk.jpg')
        qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=3,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()
        base_img.paste(qr_img, (200, 678))
        ftext = Image.open(
            settings.BASE_DIR + '/uploads/spread/' + sub_path + '/invitation_code_' + str(user.id) + '.jpg')
        base_img.paste(ftext, (310, 1080))  # 插入邀请码

        # 保存二维码图片
        qr_img.save(save_path + '/qrcode_' + str(user.id) + '.jpg')
        # qr_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/qrcode_' + str(user_id) + '.png'
        # 保存推广图片
        if self.request.GET.get('language') == 'en':
            base_img.save(save_path + '/spread_' + str(user.id) + '_new_en.jpg', quality=90)
            base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new_en.jpg'
        else:
            base_img.save(save_path + '/spread_' + str(user.id) + '_new.jpg', quality=90)
            base_img = settings.MEDIA_DOMAIN_HOST + '/spread/' + sub_path + '/spread_' + str(user.id) + '_new.jpg'

        qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)

        return self.response({'code': 0, "base_img": base_img, "qr_data": qr_data, "invitation_code": invitation_code})


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
        date = datetime.now().strftime('%Y%m%d')
        NUMBER_OF_LOTTERY_AWARDS = "number_of_lottery_Awards_" + str(user_id) + str(date)  # 再来一次次数
        NUMBER_OF_PRIZES_PER_DAY = "number_of_prizes_per_day_" + str(user_id) + str(date)  # 每天抽奖次数
        number = get_cache(NUMBER_OF_PRIZES_PER_DAY)
        if number == None:
            number = 5
            is_gratis = 0
            set_cache(NUMBER_OF_PRIZES_PER_DAY, number, 86400)
            set_cache(NUMBER_OF_LOTTERY_AWARDS, is_gratis, 86400)
        number = get_cache(NUMBER_OF_PRIZES_PER_DAY)
        is_gratis = get_cache(NUMBER_OF_LOTTERY_AWARDS)
        user_gsg = UserCoin.objects.get(user_id=user_id, coin_id=6)
        results = super().list(request, *args, **kwargs)
        list = results.data.get('results')
        prize_consume = list[0]['prize_consume']
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
            {'code': 0, 'data': data, 'is_gratis': is_gratis, 'number': number,
             'integral': normalize_fraction(user_gsg.balance, 2),
             'prize_consume': normalize_fraction(prize_consume, 2)})


class ClickLuckDrawView(CreateAPIView):
    """
    点击抽奖
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        user_info = request.user
        date = datetime.now().strftime('%Y%m%d')
        NUMBER_OF_LOTTERY_AWARDS = "number_of_lottery_Awards_" + str(user_info.pk) + str(date)  # 再来一次次数
        is_gratis = get_cache(NUMBER_OF_LOTTERY_AWARDS)
        NUMBER_OF_PRIZES_PER_DAY = "number_of_prizes_per_day_" + str(user_info.pk) + str(date)  # 每天抽奖次数
        number = get_cache(NUMBER_OF_PRIZES_PER_DAY)
        number = int(number)
        integral_all = IntegralPrize.objects.filter()
        prize_consume = integral_all[0].prize_consume
        user_gsg = UserCoin.objects.get(user_id=user_info.id, coin_id=6)
        if is_gratis != 1 and Decimal(user_gsg.balance) < Decimal(prize_consume):
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
        if int(is_gratis) == 1:
            decr_cache(NUMBER_OF_LOTTERY_AWARDS)
        elif int(is_gratis) != 1:
            decr_cache(NUMBER_OF_PRIZES_PER_DAY)
            user_gsg.balance -= Decimal(prize_consume)
            user_gsg.save()
            coin_detail = CoinDetail()
            coin_detail.user = user_info
            coin_detail.coin_name = user_gsg.coin.name
            coin_detail.amount = '-' + str(prize_consume)
            coin_detail.rest = Decimal(user_gsg.balance)
            coin_detail.sources = 4
            coin_detail.save()
        try:
            integral_prize = IntegralPrize.objects.get(prize_name=choice)
        except DailyLog.DoesNotExist:
            return 0
        if choice == "再来一次":
            incr_cache(NUMBER_OF_LOTTERY_AWARDS)

        if choice == "GSG":
            integral = Decimal(integral_prize.prize_number)
            user_gsg.balance += integral
            user_gsg.save()
            coin_detail = CoinDetail()
            coin_detail.user = user_info
            coin_detail.coin_name = user_gsg.coin.name
            coin_detail.amount = '+' + str(integral)
            coin_detail.rest = Decimal(user_gsg.balance)
            coin_detail.sources = 4
            coin_detail.save()

        CACHE_FICTITIOUS_PRIZE_NAME = "cache_fictitious_prize_name"
        fictitious_prize_name = get_cache(CACHE_FICTITIOUS_PRIZE_NAME)
        if fictitious_prize_name == None:
            fictitious_prize_name_list = IntegralPrize.objects.filter(is_delete=0, is_fictitious=1).values_list(
                'prize_name')
            fictitious_prize_name = []
            for a in fictitious_prize_name_list:
                fictitious_prize_name.append(a[0])
            set_cache(CACHE_FICTITIOUS_PRIZE_NAME, fictitious_prize_name)

        if choice in fictitious_prize_name:
            try:
                user_coin = UserCoin.objects.get(user_id=user_info.pk, coin__name=choice)
            except DailyLog.DoesNotExist:
                return 0
            user_coin.balance += Decimal(integral_prize.prize_number)
            user_coin.save()
            coin_detail = CoinDetail()
            coin_detail.user = user_info
            coin_detail.coin_name = choice
            coin_detail.amount = Decimal(integral_prize.prize_number)
            coin_detail.rest = Decimal(user_coin.balance)
            coin_detail.sources = 4
            coin_detail.save()

        integral_prize_record = IntegralPrizeRecord()
        integral_prize_record.user = user_info
        integral_prize_record.prize = integral_prize
        integral_prize_record.is_receive = 1
        integral_prize_record.save()
        prize_number = integral_prize.prize_number
        user_gsg = UserCoin.objects.get(user_id=user_info.id, coin_id=6)
        if int(integral_prize.prize_number) == 0:
            prize_number = ""
        prize_name = integral_prize.prize_name
        if self.request.GET.get('language') == 'en' and prize_name == '谢谢参与':
            prize_name = 'Thanks'
        if self.request.GET.get('language') == 'en' and prize_name == '再来一次':
            prize_name = 'Once again'
        return self.response({
            'code': 0,
            'data': {
                'id': integral_prize.id,
                'icon': integral_prize.icon,
                'prize_name': prize_name,
                'prize_number': prize_number,
                'integral': normalize_fraction(user_gsg.balance, 2),
                'number': get_cache(NUMBER_OF_PRIZES_PER_DAY),
                'is_gratis': get_cache(NUMBER_OF_LOTTERY_AWARDS)
            }
        })


class ActivityImageView(ListAPIView):
    """
    活动图片
    """

    def get(self, request, *args, **kwargs):
        now_time = datetime.now().strftime('%Y%m%d%H%M')
        language = self.request.GET.get('language')
        activity_img = '/'.join(
            [MEDIA_DOMAIN_HOST, language_switch(language, "ATI") + '.jpg?t=%s' % now_time])
        if language == 'en':
            activity = 'Recharge'
        else:
            activity = '充值福利'
        return self.response(
            {'code': 0, 'data': [{'img_url': activity_img, 'action': 'Activity', 'activity_name': activity}]})


class USDTActivityView(ListAPIView):
    """
    USDT活动图片
    """

    def get(self, request, *args, **kwargs):
        now_time = datetime.now().strftime('%Y%m%d%H%M')
        language = self.request.GET.get('language')
        usdt_img = '/'.join(
            [MEDIA_DOMAIN_HOST, language_switch(self.request.GET.get('language'), "USDT_ATI") + ".jpg?t=%s" % now_time])
        if language == 'en':
            activity = 'GIVE YOU A HAND'
        else:
            activity = '助你一币之力'
        return self.response(
            {'code': 0, 'data': [{'img_url': usdt_img, 'action': 'USDT_Activity', 'activity_name': activity}]})


class CheckInvitationCode(ListAPIView):
    """
    邀请码校验
    """

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        invitation_code = request.GET.get('invitation_code')
        invitation_code = invitation_code.upper()
        invitation_user = User.objects.filter(invitation_code=invitation_code).count()
        if invitation_user == 0:
            raise ParamErrorException(error_code.API_10109_INVITATION_CODE_NOT_NONENTITY)

        invitation_user = User.objects.get(invitation_code=invitation_code)
        # invitee_number = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=int(invitation_user.pk),
        #                                                is_deleted=1).count()
        # if invitee_number >= 5:  # 邀请T1是否已达上限
        #     raise ParamErrorException(error_code.API_10107_INVITATION_CODE_INVALID)
        return self.response({'code': 0, 'id': invitation_user.id, 'avatar': invitation_user.avatar,
                              'nickname': invitation_user.nickname})


class CountriesView(ListAPIView):
    """
    电话区号列表
    """
    serializer_class = CountriesSerialize

    def get_queryset(self):
        list = Countries.objects.filter(~Q(status=1))
        return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append({
                "id": list["id"],
                "code": list["code"],
                "area_code": list["area_code"],
                "name_en": list["name_en"],
                "name_zh_HK": list["name_zh_HK"],
                "name_zh_CN": list["name_zh_CN"],
                "language": list["language"]
            })

        return self.response({'code': 0, 'data': data})


class HomeMessageView(ListAPIView):
    """
    首页推送公告
    """
    permission_classes = (LoginRequired,)
    serializer_class = HomeMessageSerialize

    def get_queryset(self):
        list = Message.objects.filter(type=4, is_deleted=0).order_by('-created_at')
        return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append(list["message_list"])
        return self.response({'code': 0, 'data': data})

    # def get_queryset(self):
    #     pass
    #
    # def list(self, request, *args, **kwargs):
    #     sql = "select concat(a.title,': ',a.content)from users_message a"
    #     sql += " where a.type=4"
    #     sql += " and a.is_deleted=0"
    #     data = get_sql(sql)  # 用户拥有的ETH
    #     return self.response({'code': 0, 'data': data})
