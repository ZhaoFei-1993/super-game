# -*- coding: UTF-8 -*-
from rest_framework import exceptions
from rest_framework import authentication
from .authentication import SignatureAuthentication

from django.conf import settings

from rest_framework.authtoken.models import Token
import re


class CCSignatureAuthentication(SignatureAuthentication):
    """
    APP接口签名校验
    """
    def fetch_user_secret(self, api_key):
        try:
            token = settings.APP_API_KEY[api_key]
        except KeyError:
            raise exceptions.AuthenticationFailed('Bad API key')

        return 'user', token

    def fetch_user_data(self, username):
        try:
            user = User.objects.filter(username=username).order_by().get()
        except KeyError:
            raise exceptions.AuthenticationFailed('Authentication Fail')

        return user


# class CCSignatureAuthBackend(authentication.BaseAuthentication):
#     """
#     后台接口登录校验
#     """
#     SIGNATURE_RE = re.compile('token="(.+?)"')
#
#     def get_signature_from_signature_string(self, signature):
#         """Return the signature from the signature header or None."""
#         match = self.SIGNATURE_RE.search(signature)
#         if not match:
#             return None
#         return match.group(1)
#
#     @staticmethod
#     def header_canonical(header_name):
#         """Translate HTTP headers to Django header names."""
#         header_name = header_name.lower()
#         if header_name == 'content-type':
#             return 'CONTENT-TYPE'
#         elif header_name == 'content-length':
#             return 'CONTENT-LENGTH'
#         return 'HTTP_%s' % header_name.replace('-', '_').upper()
#
#     def authenticate(self, request):
#         """
#         校验
#         :param request:
#         :return:
#         """
#         authorization_header = self.header_canonical('Authorization')
#         sent_string = request.META.get(authorization_header)
#         if sent_string is None:
#             raise exceptions.AuthenticationFailed('Authentication Fail')
#
#         token_string = self.get_signature_from_signature_string(sent_string)
#
#         token = Token.objects.filter(key=token_string).values('user_id').first()
#         user_id = token['user_id']
#         admin = WccAdmin.objects.get(pk=user_id)
#         request.user = admin
#
#         return admin, token_string
