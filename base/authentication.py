# -*- coding: UTF-8 -*-
from rest_framework import authentication
from httpsig import HeaderSigner
from urllib.parse import quote_plus
import re

from rest_framework_jwt.settings import api_settings
from .exceptions import SystemParamException, SignatureNotMatchException, NotLoginException

from django.core.cache import caches

from . import code


class SignatureAuthentication(authentication.BaseAuthentication):
    """
    接口签名校验
    与外部接口，如APP、小程序接口通讯校验
    """

    SIGNATURE_RE = re.compile('signature="(.+?)"')
    SIGNATURE_TOKEN_RE = re.compile('Bearer="(.+?)"')
    SIGNATURE_HEADERS_RE = re.compile('headers="([()\sa-z0-9-]+?)"')

    API_KEY_HEADER = 'X-Api-Key'
    API_NONCE_HEADER = 'nonce'
    ALGORITHM = 'hmac-sha256'

    # 需要登录验证的URL放到这个列表内
    authenticate_url = [
        'v1/user/info/',
        'v1/user/logout/',
        'v1/user/recharge/',
        'v1/user/modifypassword/',
        'v1/quiz/comment/',
        'v1/quiz/favorite/',
        'v1/quiz/bet/',
        'v1/quiz/bet/daily/',
        'v1/quiz/bet/competition/',
        'v1/quiz/mostactiveuser/list/',
        'v1/user/feedback/',
        'v1/quiz/competition/(.+?)/join/',
        'v1/user/favorite/',
        'v1/sms/content/',
        'v1/upload/',
        'v1/quiz/records/',
        'v1/recharge/diamonds_amount_exchange/',
        'v1/quiz/comment/like/(.+?)/',
        'v1/user/quiz/',
        'v1/user/achievement/',
        'v1/user/favorite-del/(.+?)/',
        'v1/user/country_ranking/',
        'v1/user/friend_ranking/',
        'v1/user/score/',  #
        'v1/chat/clublist/',
        'v1/chat/seekfriend/',
        'v1/chat/send_friendinvitation/',
        'v1/chat/friendinvite/',
        'v1/chat/friendinvitelist/',
        'v1/chat/friendlist/',
        'v1/chat/deletefriend/',
        'v1/chat/friendinfo/',
        'v1/chat/qualification_list/',
        'v1/chat/audit_list/',
        'v1/chat/member_management_list/',
        'v1/chat/clubuser_list/',
        'v1/chat/found_club_config/',
        'v1/chat/club_invitelist/',
        'v1/chat/modify_club_config/',
        'v1/chat/found_club/',
        'v1/chat/modify_club/',
        'v1/chat/send_clubinvitation/',
        'v1/chat/dissolve_club/',
        'v1/chat/leave_oneself/',
        'v1/chat/category/',
        'v1/chat/list/',
        'v1/chat/club_notice/',
        'v1/chat/left_userinfo/',
        'v1/chat/through_audit/',
        'v1/chat/qualification/',
        'v1/chat/clubinvite/',
        'v1/chat/member_management/',
        'v1/chat/system_problem_edit/',
        'v1/chat/questions_list/',
        'v1/chat/pause_bets/',
        'v1/chat/the_topic/',
        'v1/chat/club_quiz_details/',
        'v1/chat/Club_bet/',
        'v1/chat/record_list/',
        'v1/chat/the_lottery_list/',
        'v1/chat/the_lottery/',
        'v1/chat/banker_record_list/',
        'v1/chat/clubinvitesfriendslist/',
        'v1/chat/clubbulkinvitation/',
        'v1/chat/SeekFriendList/',
        'v1/chat/deposit/',
        'v1/chat/clubnoticelist/',
        'v1/chat/clubnoticedelete/',
        'v1/chat/club_remind/',
        'v1/chat/betpower_gag_list/',
        'v1/chat/betpower/',
        'v1/chat/gag/',
        'v1/chat/damages/',
    ]
    # 未登录可访问，但登录可获取用户信息的URL列表
    unauthenticate_token_url = [
        'v1/home/',  # 首页
        'v1/quiz/competition/list/',  # 比赛列表
        'v1/quiz/daily/',  # 每日一猜
        'v1/quiz/competition/(.+?)/quiz/',  # 比赛题目列表
        'v1/quiz/(.+?)/',  # 题目详情
        'v1/quiz/commentt/(.+?)/',  # 评论列表
    ]

    def get_signature_from_signature_string(self, signature):
        """Return the signature from the signature header or None."""
        match = self.SIGNATURE_RE.search(signature)
        if not match:
            return None
        return match.group(1)

    def get_token_from_signature_string(self, signature):
        """
        获取access token
        :param signature: 
        :return: 
        """
        match = self.SIGNATURE_TOKEN_RE.search(signature)
        if not match:
            return None
        return match.group(1)

    @staticmethod
    def get_item_keys(request):
        item_keys = sorted(request.data.keys())
        keys = []
        for key in item_keys:
            if key == 'image':
                continue
            keys.append(key)
        return keys

    def get_headers_from_signature(self, request):
        """Returns a list of headers fields to sign.

        According to http://tools.ietf.org/html/draft-cavage-http-signatures-03
        section 2.1.3, the headers are optional. If not specified, the single
        value of "Date" must be used.
        """
        api_key_header = self.header_canonical(self.API_KEY_HEADER)
        api_key = request.META.get(api_key_header)

        item_keys = self.get_item_keys(request)
        if api_key == 'xcx' or api_key == 'wechat':
            headers_string = ['x-date', 'nonce'] + item_keys
        else:
            headers_string = ['date', 'nonce'] + item_keys

        return headers_string

    @staticmethod
    def header_canonical(header_name):
        """Translate HTTP headers to Django header names."""
        header_name = header_name.lower()
        if header_name == 'content-type':
            return 'CONTENT-TYPE'
        elif header_name == 'content-length':
            return 'CONTENT-LENGTH'
        return 'HTTP_%s' % header_name.replace('-', '_').upper()

    def build_dict_to_sign(self, request, signature_headers):
        """Build a dict with headers and values used in the signature.

        "signature_headers" is a list of lowercase header names.
        """
        d = {}
        for header in signature_headers:
            if header == '(request-target)':
                continue
            d[header] = request.META.get(self.header_canonical(header))

        item_keys = self.get_item_keys(request)

        for k in item_keys:
            tmp = request.data[k]
            tmp = tmp.replace(' ', '_is_space_')
            tmp = quote_plus(tmp)
            d[k] = tmp.replace('_is_space_', '%20')
        return d

    def build_signature(self, user_api_key, user_secret, request):
        """Return the signature for the request."""
        path = request.get_full_path()
        signature_headers = self.get_headers_from_signature(request)
        unsigned = self.build_dict_to_sign(request, signature_headers)
        print('unsigned = ', unsigned)

        # Sign string and compare.
        signer = HeaderSigner(
            key_id=user_api_key, secret=user_secret,
            headers=signature_headers, algorithm=self.ALGORITHM)
        signed = signer.sign(unsigned, method=request.method, path=path)

        return signed['authorization']

    def fetch_user_data(self, username):
        """获取用户信息"""
        return None

    def fetch_user_secret(self, api_key):
        """Retuns (User instance, API Secret) or None if api_key is bad."""
        return None

    def check_auth_url(self, request):
        """
        判断当前接口URL是否需要登录
        :param request: 
        :return: 
        """
        full_path = request.get_full_path()
        api_url = full_path.replace('/caicai/api/', '')
        is_need_auth = False
        for url in self.authenticate_url:
            match = re.compile(url).search(api_url)
            if match is not None:
                is_need_auth = True
                break
        return is_need_auth

    def check_unauth_token_url(self, request):
        """
        判断当前接口URL是否可获得token
        :param request: 
        :return: 
        """
        full_path = request.get_full_path()
        api_url = full_path.replace('/caicai/api/', '')
        is_need_auth_token = False
        for url in self.unauthenticate_token_url:
            match = re.compile(url).search(api_url)
            if match is not None:
                is_need_auth_token = True
                break
        return is_need_auth_token

    @staticmethod
    def print_request_data(request):
        print('=========request data begin=========')
        for key in request.data:
            print(key, ' = ', request.data[key])
        print('=========request data end=========')

    def authenticate(self, request):
        # Check for API key header.
        api_key_header = self.header_canonical(self.API_KEY_HEADER)
        api_key = request.META.get(api_key_header)
        print('api_key = ', api_key)
        if not api_key:
            raise SystemParamException(code.API_10101_SYSTEM_PARAM_REQUIRE)

        # Check if request has a "Signature" request header.
        authorization_header = self.header_canonical('Authorization')
        sent_string = request.META.get(authorization_header)
        if not sent_string:
            raise SystemParamException(code.API_10101_SYSTEM_PARAM_REQUIRE)
        sent_signature = self.get_signature_from_signature_string(sent_string)
        print('signature = ', sent_signature)

        # check if request has a "nonce" request header
        nonce_header = self.header_canonical(self.API_NONCE_HEADER)
        sent_nonce = request.META.get(nonce_header)
        if not sent_nonce:
            raise SystemParamException(code.API_10101_SYSTEM_PARAM_REQUIRE)

        # 登录验证
        sent_token = self.get_token_from_signature_string(sent_string)

        print('Bearer = ', sent_token)
        self.print_request_data(request)

        login_required = self.check_auth_url(request)
        is_need_auth_token = self.check_unauth_token_url(request)

        if login_required:
            if sent_token is None:
                raise NotLoginException(code.API_10103_LOGIN_REQUIRE)
            else:
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                try:
                    token = jwt_decode_handler(sent_token)
                    # request.user = User.objects.get(pk=token['user_id'])

                    # 判断用户token是否存在memcached中
                    cache = caches['memcached']
                    cache_key = request.user.username + api_key
                    if cache.get(cache_key) != sent_token:
                        raise NotLoginException(code.API_10103_LOGIN_REQUIRE)
                except Exception:
                    raise NotLoginException(code.API_10103_LOGIN_REQUIRE)

        if is_need_auth_token:
            if sent_token is not None:
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                token = jwt_decode_handler(sent_token)
                request.user = 'user'
                # request_user = User.objects.filter(pk=token['user_id']).count()
                # if request_user == 0:
                #     request.user = 'user'
                # else:
                    # request.user = User.objects.get(pk=token['user_id'])

                    # 判断用户token是否存在memcacheddeepin中
                    # cache = caches['memcached']
                    # cache_key = request.user.username + api_key
                    # if cache.get(cache_key) != sent_token:
                    #     request.user = 'user'

        # Fetch credentials for API key from the data store.
        try:
            user, secret = self.fetch_user_secret(api_key)
            if sent_token is not None:
                if login_required or is_need_auth_token:
                    user = request.user
        except TypeError:
            raise NotLoginException(code.API_10103_LOGIN_REQUIRE)
        # Build string to sign from "headers" part of Signature value.
        computed_string = self.build_signature(api_key, secret, request)
        computed_signature = self.get_signature_from_signature_string(
            computed_string)

        if computed_signature != sent_signature:
            print('computed_signature = ', computed_signature)
            print('sent_signature = ', sent_signature)
            raise SignatureNotMatchException(code.API_10102_SIGNATURE_ERROR)
        return user, api_key
