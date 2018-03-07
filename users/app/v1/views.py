# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, ListAPIView
from .serializers import ListSerialize, UserInfoSerializer, UserSerializer, AssetsSerialize, RankingSerialize, \
    DailySerialize
from ...models import User, UserRecharge, DailyLog, DailySettings, Coin
from base.app import CreateAPIView, ListCreateAPIView
from base.function import LoginRequired
from base import code as error_code
from sms.models import Sms
from datetime import datetime
import time
import pytz
import local_settings
from django.conf import settings
from base.exceptions import ParamErrorException

from utils.functions import random_salt, sign_confirmation, message_hints
from rest_framework_jwt.settings import api_settings

from django.db import transaction
import re


class UserRegister(object):
    """
    用户公共处理类
    """

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

    def login(self, source, username):
        """
        用户登录
        :param source:   用户来源
        :param username: 用户账号
        :param password: 登录密码，第三方登录不提供
        :return:
        """
        token = None

        user = User.objects.get(username=username)

        token = self.get_access_token(source=source, user=user)

        return token

    @transaction.atomic()
    def register(self, source, username, password, avatar='', nickname='', ):
        """
        用户注册
        :param source:      用户来源：ios、android
        :param username:    用户账号：openid
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
        user.password = password
        user.register_type = register_type
        user.avatar = avatar
        user.nickname = nickname
        user.eth_address = 10086  # ETH地址    暂时默认都是10086
        user.save()
        # 生成签到记录
        userinfo = User.objects.get(username=username)
        daily = DailyLog()
        daily.user_id = userinfo.id
        daily.number = 0
        daily.sign_date = time.strftime("%Y%m%d")
        daily.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        daily.save()
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

        username = request.data.get('username')
        avatar = request.data.get('avatar')
        nickname = request.data.get('nickname')

        password = random_salt(8)

        user = User.objects.filter(username=username)
        if len(user) == 0:
            token = ur.register(source=source, username=username, password=password,
                                avatar=avatar, nickname=nickname)
        else:
            token = ur.login(source=source, username=username)

        return self.response({
            'code': 0,
            'data': {'access_token': token, 'chat_username': username}})


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
    get方法：首页----设置页面（并用）  post方法：修改昵称
    """
    permission_classes = (LoginRequired,)
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user_id = self.request.user.id
        sing = sign_confirmation(user_id)  # 是否签到
        message = message_hints(user_id)  # 是否有未读消息

        return self.response({
            'code': 0,
            'user_id': items[0]["id"],
            'nickname': items[0]["nickname"],
            'avatar': items[0]["avatar"],
            'meth': items[0]["meth"],
            'ggtc': items[0]["ggtc"],
            'is_sound': items[0]["is_sound"],
            'is_notify': items[0]["is_notify"],
            'telephone': items[0]["telephone"],
            'pass_code': items[0]["pass_code"],
            'message': message,
            'sing': sing})

    def _update_info(self, request):
        """
        修改昵称
        """
        user = request.user
        if "avatar" in request.data:
            user.avatar = request.data.get("avatar")
        if "nickname" in request.data:
            user.nickname = request.data.get("nickname")
        user.save()
        content = {'code': 0}
        return self.response(content)

    def post(self, request, *args, **kwargs):

        return self._update_info(request)


class AssetsView(ListAPIView):
    """
    我的资产
    """
    permission_classes = (LoginRequired,)
    serializer_class = AssetsSerialize

    def get_queryset(self):
        return UserRecharge.objects.get(user_id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        userinfo = UserRecharge.objects.get(user_id=self.request.user.id)
        print("userinfo==========", userinfo)

        return self.response({
            'code': 0,
        })


class RankingView(ListAPIView):
    """
    排行榜
    """
    permission_classes = (LoginRequired,)
    serializer_class = RankingSerialize

    def get_queryset(self):
        return User.objects.all().order_by('id')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        user = request.user
        user_arr = User.objects.all().values_list('id').order_by('id')[:100]
        my_ran = "未上榜"
        index = 0
        for i in user_arr:
            index = index + 1
            if i[0] == user.id:
                my_ran = index
        data = []
        if 'page' not in request.GET:
            page = 1
        else:
            page = int(request.GET.get('page'))
        i = (page - 1) * 10
        for fav in Progress:
            i = i + 1
            user_id = fav.get('id')
            data.append({
                'user_id': user_id,
                'avatar': fav.get('avatar'),
                'nickname': fav.get('nickname'),
                'ranking': i,
            })

        avatar = user.avatar
        nickname = user.nickname
        my_ranking = {
            "id": user.id,
            "avatar": avatar,
            "nickname": nickname,
            "ranking": my_ran
        }

        return self.response({'code': 0, 'data': data, 'my_ranking': my_ranking})


class SecurityView(ListCreateAPIView):
    """
     密保校验 用户绑定密保  and   修改密保
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        type = kwargs['type']
        pass_code = request.data.get('pass_code')
        if "pass_code" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20106_PASS_CODE_ERROR)

        user = User.objects.get(id=self.request.user.id)
        if int(type) == 1:
            if int(user.pass_code) != int(pass_code):
                raise ParamErrorException(error_code=error_code.API_20106_PASS_CODE_ERROR)
        elif int(type) == 2:
            if int(user.pass_code) == int(pass_code):
                raise ParamErrorException(error_code=error_code.API_20107_ALIKE_PASS_CODE)
            else:
                user.pass_code = pass_code
                user.save()
        content = {'code': 0}
        return self.response(content)


class BackSecurityView(ListCreateAPIView):
    """
     忘记密保
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        telephone = request.data.get('telephone')
        pass_code = request.data.get('pass_code')

        if "pass_code" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20106_PASS_CODE_ERROR)
        if "sms_code" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20104_SMS_CODE_INVALID)
        message = Sms.objects.filter(telephone=telephone, code=request.data.get('sms_code')).first()
        if message is None:
            raise ParamErrorException(error_code=error_code.API_20104_SMS_CODE_INVALID)

        # 短信发送时间
        code_time = message.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        code_time = time.mktime(code_time.timetuple())
        current_time = time.mktime(datetime.datetime.now().timetuple())

        # 判断code是否过期
        if (settings.SMS_CODE_EXPIRE_TIME > 0) and (current_time - code_time > settings.SMS_CODE_EXPIRE_TIME):
            return self.response({'code': error_code.API_20105_SMS_CODE_EXPIRED})

        message = Sms.objects.filter(telephone=telephone, code=request.data.get('sms_code')).first()
        if message is None:
            raise ParamErrorException(error_code=error_code.API_20104_SMS_CODE_INVALID)

        user = User.objects.get(id=self.request.user.id)
        user.pass_code = pass_code
        user.save()
        content = {'code': 0}
        return self.response(content)


class SwitchView(ListCreateAPIView):
    """
    音效/消息免推送 开关
    """

    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
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

        user = User.objects.get(id=self.request.user.id)
        if int(event) == 0:
            user.is_sound = status
        else:
            user.is_notify = status
        user.save()
        content = {'code': 0}
        return self.response(content)


class ListView(FormatListAPIView):
    """
    返回用户列表
    """
    serializer_class = ListSerialize
    queryset = User.objects.all()


class DailyView(ListAPIView):
    """
    get方法：签到列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = DailySerialize

    def get_queryset(self):
        daily = DailySettings.objects.all()
        return daily

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        sing = sign_confirmation(user_id)  # 判断是否签到
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')

        content = {'code': 0,
                   "items": items,
                   "sing": sing,  # 今天是否签到
                   }
        return self.response(content)

    def _update_info(self, request):
        """
        post方法：点击签到
        """
        user_id = self.request.user.id
        sing = sign_confirmation(user_id)  # 判断是否签到
        if sing == 1:
            raise ParamErrorException(error_code.API_30105_ALREADY_SING)
        user = User.objects.get(pk=user_id)
        daily = DailyLog.objects.get(user_id=user_id)
        if int(daily.number) == 6:
            fate = 0
            daily.number = 0
        else:
            fate = daily.number + 1
            daily.number += 1
        dailysettings = DailySettings.objects.get(days=fate)
        rewards = dailysettings.rewards
        coin = dailysettings.coin.type
        if int(coin) == 1:
            user.ggtc += rewards
            user.save()
        elif int(coin) == 2:
            user.meth += rewards
            user.save()
        daily.sign_date = time.strftime("%Y%m%d")
        daily.save()

        content = {'code': 0,
                   "rewards": rewards,
                   }
        return self.response(content)

    def post(self, request, *args, **kwargs):

        return self._update_info(request)
