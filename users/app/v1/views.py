# -*- coding: UTF-8 -*-
from django.db.models import Q
from base.app import ListAPIView, DestroyAPIView
from .serializers import UserInfoSerializer, UserSerializer, \
    DailySerialize, MessageListSerialize
from ...models import User, DailyLog, DailySettings, UserMessage, Message
from base.app import CreateAPIView, ListCreateAPIView
from base.function import LoginRequired
from base import code as error_code
from sms.models import Sms
from datetime import timedelta, datetime
import time
import pytz
from django.conf import settings
from base.exceptions import ParamErrorException
from utils.functions import random_salt, sign_confirmation, message_hints, \
    message_sign, amount, value_judge
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

        try:
            user = User.objects.get(username=username)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

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
        user.register_type = register_type
        user.avatar = avatar
        user.nickname = nickname
        user.eth_address = 10086  # ETH地址    暂时默认都是10086
        user.save()
        # 生成签到记录
        try:
            userinfo = User.objects.get(username=username)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
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
        value = value_judge(request, "username")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
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
            'data': {'access_token': token, }})


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
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user_id = self.request.user.id
        is_sign = sign_confirmation(user_id)  # 是否签到
        is_message = message_hints(user_id)  # 是否有未读消息
        ggtc_locked = amount(user_id)  # 该用户锁定的金额

        return self.response({
            'code': 0,
            'user_id': items[0]["id"],
            'nickname': items[0]["nickname"],
            'avatar': items[0]["avatar"],
            'eth_address': items[0]["eth_address"],
            'meth': items[0]["meth"],
            'ggtc': items[0]["ggtc"],
            'telephone': items[0]["telephone"],
            'is_passcode': items[0]["is_passcode"],
            'ggtc_locked': ggtc_locked,
            'is_message': is_message,
            'is_sign': is_sign})


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

        content = {'code': 0}
        return self.response(content)


class BindTelephoneView(ListCreateAPIView):
    """
    绑定手机
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, "telephone","code")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        telephone = request.data.get('telephone')
        if "code" not in request.data:
            raise ParamErrorException(error_code=error_code.API_20401_TELEPHONE_ERROR)

        # 获取该手机号码最后一条发短信记录
        sms = Sms.objects.filter(telephone=telephone).order_by('-id').first()
        if (sms is None) or (sms.code != request.data.get('code')):
            return self.response({'code': error_code.API_20402_INVALID_SMS_CODE})

        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.datetime.now().timetuple())
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

        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.datetime.now().timetuple())
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
        return User.objects.all().order_by('-victory','id')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        user = request.user
        user_arr = User.objects.all().values_list('id').order_by('-victory','id')[:100]
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
                'win_ratio': fav.get('win_ratio'),
                'ranking': i,
            })
            data.sort(key=lambda x: x["ranking"])

        avatar = user.avatar
        nickname = user.nickname
        win_ratio = user.victory
        if user.victory==0:
            win_ratio = 0
        my_ranking = {
            "id": user.id,
            "avatar": avatar,
            "nickname": nickname,
            "win_ratio": str(win_ratio) + "%",
            "ranking": my_ran
        }

        return self.response({'code': 0, 'data': data, 'my_ranking': my_ranking})


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
        if int(passcode) != int(user.pass_code):
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

        # 判断验证码是否已过期
        sent_time = sms.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = time.mktime(datetime.datetime.now().timetuple())
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
        daily = DailySettings.objects.all()
        return daily

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        sign = sign_confirmation(user_id)  # 判断是否签到
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        try:
            daily = DailyLog.objects.get(user_id=user_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        is_sign = 0
        data = []
        for list in items:
            if list["days"] < daily.number or list["days"] == daily.number:
                is_sign = 1
            if sign == 1 and daily.number == 0:
                is_sign = 1
            data.append({
                "id": list["id"],
                "days": list["days"],
                "rewards": list["rewards"],
                "is_sign": is_sign
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
        yesterday_format = yesterday.strftime('%Y%m%d')
        if sign == 1:
            raise ParamErrorException(error_code.API_30201_ALREADY_SING)
        try:
            user = User.objects.get(pk=user_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            daily = DailyLog.objects.get(user_id=user_id)
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        if daily.sign_date != yesterday_format:  # 判断昨天签到没有
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
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
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
                "message_id": list["id"],
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
        UserMessage.objects.filter(user_id=user,message_id=message_id).update(status=1)
        content = {'code': 0,
                   'content': message.content}
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