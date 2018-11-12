# -*- coding: UTF-8 -*-
from rest_framework import authentication
from httpsig import HeaderSigner
from urllib.parse import quote_plus
import re
import time
import dateutil.parser as dateparser

from rest_framework_jwt.settings import api_settings
from .exceptions import SystemParamException, SignatureNotMatchException, NotLoginException

from django.conf import settings

from . import code

from users.models import User
from base import code as error_code
from base.exceptions import ParamErrorException
from utils.cache import get_cache, set_cache
from wc_auth.models import Admin


class SignatureAuthentication(authentication.BaseAuthentication):
    """
    接口签名校验
    与外部接口，如APP、小程序接口通讯校验
    """

    SIGNATURE_RE = re.compile('signature="(.+?)"')
    SIGNATURE_TOKEN_RE = re.compile('Bearer="(.+?)"')
    SIGNATURE_HEADERS_RE = re.compile('headers="([()\sa-z0-9-]+?)"')

    API_KEY_HEADER = 'X-Api-Key'
    API_NONCE_HEADER = 'X-Nonce'
    ALGORITHM = 'hmac-sha256'

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
        self.group = match.group(1)
        return self.group

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
        date_key = 'date'
        if api_key == 'HTML5' or api_key == 'MINIPROGRAM':
            date_key = 'x-date'

        headers_string = [date_key, 'x-nonce'] + item_keys
        print('headers_string = ', headers_string)

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
            tmp = str(request.data[k])
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

        # 获取语言数据
        language = 'cn'
        if 'language' in request.GET:
            language = request.GET.get('language')
        request.language = language

        print('request.language = ', request.language)

        # 60秒以前的请求不再处理
        date_key = 'date'
        if api_key == 'HTML5' or api_key == 'MINIPROGRAM':
            date_key = 'x-date'
        date_header = self.header_canonical(date_key)
        api_date = request.META.get(date_header)
        print('date = ', api_date)
        api_date_dt = dateparser.parse(api_date)
        api_date_timestamp = time.mktime(api_date_dt.timetuple()) + 8 * 3600
        # if api_date_timestamp + 300 < time.time():
        #     raise SystemParamException(code.API_10103_REQUEST_EXPIRED)
            # pass  # TODO: remove it!!!!

        # Check if request has a "Signature" request header.
        authorization_header = self.header_canonical('Authorization')
        sent_string = request.META.get(authorization_header)
        # if not sent_string:
        #     raise SystemParamException(code.API_10101_SYSTEM_PARAM_REQUIRE)
        sent_signature = self.get_signature_from_signature_string(sent_string)
        print('signature = ', sent_signature)

        # check if request has a "nonce" request header
        nonce_header = self.header_canonical(self.API_NONCE_HEADER)
        sent_nonce = request.META.get(nonce_header)
        # print('x-nonce = ', sent_nonce)
        # if not sent_nonce:
        #     raise SystemParamException(code.API_10101_SYSTEM_PARAM_REQUIRE)

        # TODO: prevent replay request!!!，把nonce传入缓存中，60秒有效，60秒内如果有相同的nonce值，则deny
        # if get_cache('api_nonce') == sent_nonce:
        #     raise SystemParamException(code.API_10110_REQUEST_REPLY_DENY)
        #     pass
        # set_cache('api_nonce', sent_nonce, 60)

        # 登录验证
        sent_token = self.get_token_from_signature_string(sent_string)

        print('Bearer = ', sent_token)
        self.print_request_data(request)

        if sent_token is not None:
            try:
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                token = jwt_decode_handler(sent_token)
                if api_key == 'MINIPROGRAM':
                    if 'HTTP_OP' in request.META:
                        request.user = Admin.objects.get(pk=token['user_id'])
                    else:
                        request.user = User.objects.get(pk=token['user_id'])
                else:
                    request.user = User.objects.get(pk=token['user_id'])
            except Exception:
                raise NotLoginException(code.API_403_ACCESS_DENY)
            if api_key != 'MINIPROGRAM':
                if request.user.is_block == 1:
                    raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)

        # Fetch credentials for API key from the data store.
        try:
            user, secret = self.fetch_user_secret(api_key)
            if sent_token is not None:
                user = request.user
        except TypeError:
            raise NotLoginException(code.API_406_LOGIN_REQUIRE)
        # Build string to sign from "headers" part of Signature value.
        print(api_key,secret)
        computed_string = self.build_signature(api_key, secret, request)
        computed_signature = self.get_signature_from_signature_string(
            computed_string)

        if settings.VERIFY_SIGNATURE and computed_signature != sent_signature:
            print('computed_signature = ', computed_signature)
            print('sent_signature = ', sent_signature)
            # raise SignatureNotMatchException(code.API_10102_SIGNATURE_ERROR)
        return user, api_key
