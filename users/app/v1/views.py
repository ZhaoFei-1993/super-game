# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from base.function import LoginRequired
from django.core.cache import caches
from .serializers import ListSerialize, UserInfoSerializer, UserSerializer
from utils.functions import random_salt
from ...models import User, UserMessage
from base.app import ListAPIView, ListCreateAPIView, DestroyAPIView, CreateAPIView
from base.BaseAES import BaseAES

from rest_framework_jwt.settings import api_settings




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
        register_type = User.REGISTER_UNKNOWN
        if len(username) == 11:
            register_type = User.REGISTER_TELEPHONE
        elif len(username) == 32:
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

        # 以用户名+用户来源（iOS、Android）为key，保存到缓存中
        cache_key = user.username + source
        self.set_user_cache(cache_key, token)

        return token


class ListView(FormatListAPIView):
    """
    返回用户列表
    """
    serializer_class = ListSerialize
    queryset = User.objects.all()


class InfoView(FormatRetrieveAPIView):
    """
    获取用户信息
    """
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        news=UserMessage.objects.filter(status=0)
        newss=0
        if len(news)>0:
            newss=1




class LoginView(CreateAPIView):
    """
    用户登录
    """
    def post(self, request, *args, **kwargs):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        user = User.objects.get(pk=1)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return self.response({
            'code': 0,
            'data': {
                'access_token': token,
            }
        })


class LoginView(ListCreateAPIView):
    """
    用户登录：手机号＋密码、第三方登录
    """
    serializer_class = UserSerializer

    @staticmethod
    def _get_info(param, request):
        val = ''
        if param in request.data:
            val = request.data.get(param)

        return val

    def post(self, request, *args, **kwargs):
        """
        用户登录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        source = request.META.get('HTTP_X_API_KEY')
        ur = UserRegister()

        username = request.data.get('username')

        # 私钥解密密码串
        if 'password' in request.data and request.data['password'] != '':
            aes = BaseAES(source=source)
            password = aes.decrypt(request.data.get('password'))
        else:
            password = random_salt(8)
        user_info = User.objects.filter(username=username).values('id').order_by()

        # 第三方登录
        if 'avatar' in request.data and 'nickname' in request.data:
            unionid = ""
            user_info_union = []
            if 'unionid' in request.data:  # 空判
                unionid = request.data.get('unionid')
                if unionid != '':
                    user_info_union = User.objects.filter(unionid=unionid).values('id')

            # 修复旧数据因APP与微信公众号关联生成unionid发生的错误
            if len(user_info) > 0 and len(user_info_union) == 0:
                User.objects.filter(username=username).update(unionid=unionid)
                user_info = User.objects.filter(username=username).values('id').order_by()

            # 判断用户是否已经注册
            if len(user_info) == 0:
                avatar = request.data.get('avatar')
                nickname = request.data.get('nickname')
                device_token = ""
                if 'device_token' in request.data:
                    device_token = request.data.get('device_token')
                info = {
                    'province': self._get_info('province', request),
                    'city': self._get_info('city', request),
                    'district': self._get_info('district', request),
                    'address': self._get_info('address', request),
                    'os_version': self._get_info('os_version', request),
                    'language': self._get_info('language', request),
                    'model': self._get_info('model', request),
                    'resolution': self._get_info('resolution', request),
                    'screen_size': self._get_info('screen_size', request),
                }
                # 注册，返回access_token
                token = ur.register(source=source, username=username, password=password,
                                    avatar=avatar, nickname=nickname, device_token=device_token, unionid=unionid,
                                    info=info)
            else:
                # 登录，返回access_token
                register_type = UserRegister.get_register_type(username)
                if register_type == User.REGISTER_WECHAT and unionid != '':
                    username = unionid
                token = ur.login(source=source, username=username)
        else:
            token = ur.login(source=source, username=username, password=password)

        # 更新用户的device_token
        if 'device_token' in request.data and len(user_info) > 0:
            device_token = request.data.get('device_token')
            User.objects.filter(id=user_info[0]['id']).update(device_token=device_token)

        user = User.objects.get(username=request.data.get('username'))
        login_platfor = 2
        if source != 'android':
            login_platfor = 1

        user_login_platfor = user.login_platfor
        if int(user_login_platfor) == 0:
            User.objects.filter(pk=user.id).update(login_platfor=login_platfor)
        elif int(user_login_platfor)!=login_platfor:
            User.objects.filter(pk=user.id).update(login_platfor=login_platfor)


        chat_password = user.password
        return self.response(
            {'code': 0, 'data': {'access_token': token, 'chat_username': request.data.get('username'),
                                 'chat_password': chat_password}})
