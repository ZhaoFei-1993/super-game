# -*- coding: UTF-8 -*-
from django.db.models import Q
from .serializers import UserInfoSerializer, UserSerializer, \
    DailySerialize, MessageListSerialize, PresentationSerialize, AssetSerialize, UserCoinSerialize
from quiz.app.v1.serializers import QuizSerialize
from ...models import User, DailyLog, DailySettings, UserMessage, Message
from quiz.models import Quiz
from ...models import User, DailyLog, DailySettings, UserMessage, Message, UserCoinLock, \
    CoinLock, UserPresentation, UserCoin, Coin, \
    UserCoinLock, UserSettingOthors
from base.app import CreateAPIView, ListCreateAPIView, FormatListAPIView, ListAPIView, DestroyAPIView
from base.function import LoginRequired
from base.function import randomnickname
from sms.models import Sms
from datetime import timedelta, datetime
import time
import pytz
from django.conf import settings
from base import code as error_code
from base.exceptions import ParamErrorException, UserLoginException
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

    def login(self, source, username, password=None):
        """
        用户登录
        :param source:   用户来源
        :param username: 用户账号
        :param password: 登录密码，第三方登录不提供
        :return:
        """
        token = None

        if password is not None:
            try:
                user = User.objects.get(username=username)
            except Exception:
                raise UserLoginException(error_code=error_code.API_20103_TELEPHONE_UNREGISTER)
            if user.check_password(password):
                token = self.get_access_token(source=source, user=user)
            else:
                raise UserLoginException(error_code=error_code.API_20104_LOGIN_ERROR)
        else:
            try:
                user = User.objects.get(username=username)
            except Exception:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
            message = Message.objects.filter(type=1, created_at__gte=user.created_at)
            for i in message:
                message_id = i.id
                user_message = UserMessage.objects.filter(message=message_id, user=user.id)
                if len(user_message) == 0:
                    usermessage = UserMessage()
                    usermessage.user = user
                    usermessage.message = i
                    usermessage.save()

            coin = Coin.objects.all()
            for i in coin:
                userbalance = UserCoin.objects.filter(coin_id=i.pk, user_id=user.id).count()
                if userbalance == 0:
                    usercoin = UserCoin()
                    usercoin.user_id = user.id
                    usercoin.coin_id = i.id
                    usercoin.is_opt = False
                    usercoin.save()

            token = self.get_access_token(source=source, user=user)

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
            gsg = Coin.TYPE_CHOICE[0][1]
            is_coin = Coin.TYPE_CHOICE[1][1]
            if i.name == is_coin:
                usercoin.is_opt = True
                usercoin.address = 1008611
            if i.name == gsg:
                usercoin.is_bet =True
                usercoin.address = 0
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
        value = value_judge(request, "username")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        username = request.data.get('username')
        avatar = settings.STATIC_DOMAIN_HOST + "/images/avatar.png"
        nickname = randomnickname()
        if source != "HTML5":
            nickname = request.data.get('nickname')
            avatar = request.data.get('avatar')
        password = None
        if 'password' in request.data:
            password = request.data.get('password')

        user = User.objects.filter(username=username)
        if len(user) == 0:
            password = random_salt(8)
            token = ur.register(source=source, username=username, password=password,
                                avatar=avatar, nickname=nickname)
        else:
            token = ur.login(source=source, username=username, password=password)

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

        return self.response({'code': 0, 'data': {
            'user_id': items[0]["id"],
            'nickname': items[0]["nickname"],
            'avatar': items[0]["avatar"],
            'usercoin': items[0]["usercoin"],
            'usercoin_avatar': items[0]["usercoin_avatar"],
            'ggtc': items[0]["ggtc"],
            'ggtc_avatar': items[0]["ggtc_avatar"],
            'telephone': items[0]["telephone"],
            'is_passcode': items[0]["is_passcode"],
            'ggtc_locked': ggtc_locked,
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
        return User.objects.all().order_by('-victory', 'id')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        user = request.user
        user_arr = User.objects.all().values_list('id').order_by('-victory', 'id')[:100]
        my_ran = "未上榜"
        index = 0
        for i in user_arr:
            index = index + 1
            if i[0] == user.id:
                my_ran = index
        avatar = user.avatar
        nickname = user.nickname
        win_ratio = user.victory
        if user.victory == 0:
            win_ratio = 0
        my_ranking = {
            "id": user.id,
            "avatar": avatar,
            "nickname": nickname,
            "win_ratio": str(win_ratio) + "%",
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
                'win_ratio': fav.get('win_ratio'),
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
            if sign == 1 and daily.number == 0:
                is_sign = 1
            else:
                if list["days"] < daily.number or list["days"] == daily.number:
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
        yesterday_format = yesterday.strftime("%Y%m%d")
        yesterday_format = str(yesterday_format)+"000000"
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
        sign_date = daily.sign_date.strftime("%Y%m%d%H%M%S")
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
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        rewards = dailysettings.rewards
        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=dailysettings.coin)
        usercoin.balance += rewards
        usercoin.save()
        daily.sign_date = time.strftime('%Y-%m-%d %H:%M:%S')
        daily.save()
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
        Progress = results.data.get('results')
        data = []
        for list in Progress:
            data.append({
                "id": list["id"],
                'name': list["name"],
                'icon': list["icon"],
                'lock_ggtc': list["lock_ggtc"],
                'total': list["total"],
                'aglie':list["aglie"],
                'coin_name':list["coin_name"],
                'coin':list["coin"],
                'coin_number':list["coin_number"],
                'exchange_rate': list["exchange_rate"],
                'address': list["address"]
            })
        return self.response({'code': 0, 'data': data})


class AssetLockView(CreateAPIView):
    """
    资产锁定
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'locked_days', 'amounts')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        userid = self.request.user.id
        userinfo = User.objects.get(id=userid)
        amounts = request.data.get('amounts')
        locked_days = request.data.get('locked_days')
        # passcode = request.data.get('passcode')
        coin = Coin.objects.get(type=1)
        try:
            coin_configs = \
                CoinLock.objects.filter(period=locked_days, is_delete=0, Coin_id=coin.id).order_by('-created_at')[0]
        except Exception:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        # if passcode == '' and int(passcode) != int(userinfo.pass_code):
        #     raise ParamErrorException(error_code.API_21401_USER_PASS_CODE_ERROR)

        user_coin = UserCoin.objects.get(user_id=userid, coin_id=coin.id)
        if int(amounts) > int(user_coin.balance) or int(amounts) == 0:
                # or int(amounts) > int(coin_configs.limit_end) \
                # or int(amounts) < int(coin_configs.limit_start) \

            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_coin.balance -= int(amounts)
        user_coin.save()
        ulcoin = UserCoinLock()
        ulcoin.user = userinfo
        ulcoin.amount = int(amounts)
        ulcoin.coin_lock = coin_configs
        ulcoin.save()
        new_log = UserCoinLock.objects.filter(user_id=userid).order_by('-created_at')[0]
        new_log.end_time = new_log.created_at + timedelta(days=int(locked_days))
        new_log.save()
        content = {'code': 0}
        return self.response(content)


class UserPresentationView(CreateAPIView):
    """
    币种提现
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        value = value_judge(request, 'p_address', 'p_amount', 'c_id')
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        userid = self.request.user.id
        userinfo = User.objects.get(pk=userid)
        # passcode = request.data.get('passcode')
        p_address = request.data.get('p_address')
        c_id = request.data.get('c_id')  # p_type需要大于1,因为1为GGTC币种
        if int(c_id) <= 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        try:
            coin = Coin.objects.get(id=int(c_id))
        except Exception:
            raise
        user_coin = UserCoin.objects.get(user_id=userid, coin_id=coin.id)
        p_amount = eval(request.data.get('p_amount')) * coin.exchange_rate

        # if int(passcode) != int(userinfo.pass_code):
        #     raise ParamErrorException(error_code.API_21401_USER_PASS_CODE_ERROR)

        if p_amount > user_coin.balance or p_amount <= 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        if p_address == '':
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        user_coin.balance -= p_amount
        user_coin.save()
        presentation = UserPresentation()
        presentation.user = userinfo
        presentation.coin = coin
        presentation.amount = p_amount
        try:
            presentation.rest = user_coin.balance / coin.exchange_rate
        except Exception:
            raise
        presentation.address = p_address
        presentation.save()
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
        if c_id <= 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            coin = Coin.objects.get(id=c_id)
        except Exception:
            raise
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
                    'amount': x['amount'],
                    'rest': x['rest'],
                    'created_at': x['created_at'].split(' ')[0].replace('-','/')
                }
            )
        return self.response({'code': 0, 'data': data})


class ReviewListView(ListAPIView):
    """
    提现审核情况
    """

    permission_classes = (LoginRequired,)
    serializer_class = PresentationSerialize

    def get_queryset(self):
        userid = self.request.user.id
        c_id = int(self.kwargs['c_id'])
        if c_id <= 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        try:
            coin = Coin.objects.get(id=c_id)
        except Exception:
            raise
        query = UserPresentation.objects.filter(user_id=userid, coin_id=coin.id)
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        STATUS = ["申请中", "已处理", "已拒绝"]
        for x in items:
            data.append(
                {
                    'id': x['id'],
                    'coin_id': x['coin'],
                    'amount': x['amount'],
                    'status': STATUS[x['status']],
                    'status_code': x['status'],
                    'created_at': x['created_at'].split(' ')[0].replace('-','/')
                }
            )
        return self.response({'code': 0, 'data': data})


class LockListView(ListAPIView):
    """
    锁定记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = AssetSerialize

    def get_queryset(self):
        userid = self.request.user.id
        query = UserCoinLock.objects.filter(user_id=userid)
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for x in items:
            # if x['end_time'] >= x['created_at']:
            data.append(
                {

                    'id': x['id'],
                    'created_at': x['created_at'].split(' ')[0].replace('-','/'),
                    'amount': x['amount'],
                    'time_delta': x['time_delta']
                }
            )
        return self.response({'code': 0, 'data': data})


class DividendView(ListAPIView):
    """
    锁定金额分红记录
    """

    permission_classes = (LoginRequired,)
    serializer_class = AssetSerialize

    def get_queryset(self):
        userid = self.request.user.id
        # now = datetime.now()
        query = UserCoinLock.objects.filter(user_id=userid, is_free=1)  # USE_TZ = True时,可直接用now比较,否则now=datetime.utcnow()
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        # now = datetime.now()
        data = []
        for x in items:
            # end_time = datetime.strptime(x['end_time'], '%Y-%m-%dT%H:%M:%S+08:00')
            # if now > end_time:
            dividend = int(x['amount']) * float(x['profit'])
            data.append(
                {
                    'id': x['id'],
                    'amount': x['amount'],
                    'period': x['period'],
                    'dividend': round(dividend, 2),
                    'created_at': x['created_at'].split(' ')[0].replace('-','/'),
                    'end_time': x['end_time'].split(' ')[0].replace('-','/')
                }
            )
        return self.response({'code': 0, 'data': data})


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
        data = UserSettingOthors.objects.get(reg_type=r_type)
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
        elif int(index) == 2:
            used.is_bet = 0
            new.is_bet = 1
        used.save()
        new.save()
        content = {'code': 0}
        return self.response(content)
