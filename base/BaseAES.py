# -*- coding: UTF-8 -*-
from django.conf import settings
from Crypto.Cipher import AES
import base64
import json


class BaseAES(object):
    """
    access_token加解密
    """
    key = None
    iv = None

    def __init__(self, source):
        self.key = settings.USER_TOKEN_KEY[source]['key']
        self.iv = settings.USER_TOKEN_KEY[source]['iv']

    def encrypt(self, data):
        """
        加密
        :param data: 需要加密的字符串
        :return: 
        """
        BS = AES.block_size
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = base64.b64encode(cipher.encrypt(pad(data))).decode()

        return encrypted

    def decrypt(self, encrypted):
        """
        解密
        :param encrypted: 需要解密的字符串
        :return: 
        """
        unpad = lambda s: s[0:-ord(s[-1])]
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        data = base64.b64decode(encrypted)

        return unpad(cipher.decrypt(data).decode())
