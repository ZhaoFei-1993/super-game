# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, ListAPIView
from .serializers import ListSerialize, UserInfoSerializer, UserSerializer
from ...models import User
from base.app import CreateAPIView, ListCreateAPIView
from base.function import LoginRequired
from base.BaseAES import BaseAES

from utils.functions import random_salt, sign_confirmation,message_hints
from rest_framework_jwt.settings import api_settings

from django.db import transaction


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

        if 'password' in request.data and request.data['password'] != '':
            aes = BaseAES(source=source)
            password = aes.decrypt(request.data.get('password'))
        else:
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
    用户信息
    """
    permission_classes = (LoginRequired, )
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user_id = self.request.user.id
        sing = sign_confirmation(user_id)            # 是否签到
        message = message_hints(user_id)            # 是否有未读消息

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

    class ListView(FormatListAPIView):
        """
        返回用户列表
        """
        serializer_class = ListSerialize
        queryset = User.objects.all()



