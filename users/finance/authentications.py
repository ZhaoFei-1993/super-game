# -*- coding: UTF-8 -*-
from rest_framework import authentication
from rest_framework_jwt.settings import api_settings
from base.exceptions import SystemParamException, NotLoginException
from wc_auth.models import Admin
from base import code as error_code
from base.exceptions import ParamErrorException
from utils.cache import get_cache, set_cache
import re


class TokenAuthentication(authentication.BaseAuthentication):
    """
    接口token校验
    """
    SIGNATURE_RE = re.compile('token="(.+?)"')

    def get_signature_from_signature_string(self, signature):
        """Return the signature from the signature header or None."""
        match = self.SIGNATURE_RE.search(signature)

        if not match:
            return None
        return match.group(1)

    @staticmethod
    def header_canonical(header_name):
        """Translate HTTP headers to Django header names."""
        header_name = header_name.lower()
        if header_name == 'content-type':
            return 'CONTENT-TYPE'
        elif header_name == 'content-length':
            return 'CONTENT-LENGTH'
        return 'HTTP_%s' % header_name.replace('-', '_').upper()

    def authenticate(self, request):
        # Check if request has a "Signature" request header.
        authorization_header = self.header_canonical('Authorization')
        # 登录验证
        sent_token = request.META.get(authorization_header)
        sent_token = self.get_signature_from_signature_string(sent_token)

        print('token = ', sent_token)

        if sent_token is not None:
            try:
                jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
                token = jwt_decode_handler(sent_token)
                request.user = Admin.objects.get(username=token['username'])
                print(request.user)
            except Exception:
                raise NotLoginException(error_code.API_406_LOGIN_REQUIRE)
            # if request.user.is_block == 1:
            #     raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)]
        else:
            raise NotLoginException(error_code.API_406_LOGIN_REQUIRE)
        return request.user,token
