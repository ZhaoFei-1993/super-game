# -*- coding: UTF-8 -*-
"""
以太坊钱包处理接口类
"""
import requests
import datetime
from Crypto.Hash import HMAC, SHA256
import base64

import local_settings
from base.function import random_string, sort_object, urlencode


class Wallet(object):
    """
    钱包处理类
    """

    @staticmethod
    def get_header():
        """
        接口公共头部参数
        :return:
        """
        return {
            'X-Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Nonce': random_string()
        }

    def signature(self, headers, data=None):
        """
        获取签名值
        :param headers
        :param data:
        :return:
        """
        unsign = 'x-date:' + headers['X-Date'] + 'x-nonce:' + headers['X-Nonce']
        if data is not None:
            data = sort_object(data)
            for k in data:
                unsign += k + ':' + urlencode(data[k])

        secret = local_settings.ETH_WALLET_API_SECRET.encode('ascii')

        hash_hmac = HMAC.new(secret, digestmod=SHA256)
        hash_hmac.update(unsign.encode('ascii'))
        signed = hash_hmac.digest()
        hash_sign = base64.b64encode(signed).decode('ascii')

        return hash_sign

    def request_headers(self, data=None):
        """
        curl 请求封装方法
        :return:
        """
        headers = self.get_header()
        headers['Authorization'] = 'signature="' + self.signature(headers, data) + '"'

        return headers

    def post(self, url, data):
        """
        发起post请求
        :return:
        """
        result = requests.post(local_settings.ETH_WALLET_API_URL + url, headers=self.request_headers(data))
        return result.json()

    def get(self, url):
        """
        发起get请求
        :return:
        """
        print(self.request_headers())
        result = requests.get(local_settings.ETH_WALLET_API_URL + url, headers=self.request_headers())
        return result
