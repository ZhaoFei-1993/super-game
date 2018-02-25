# -*- coding: UTF-8 -*-
"""
接口错误码
"""
API_0_SUCCESS = 0
API_404_NOT_FOUND = 404
API_10101_SYSTEM_PARAM_REQUIRE = 10101
API_10102_SIGNATURE_ERROR = 10102
API_10103_LOGIN_REQUIRE = 10103

API_ERROR_MESSAGE = {
    API_0_SUCCESS: '请求成功',
    API_404_NOT_FOUND: '无数据',
    API_10101_SYSTEM_PARAM_REQUIRE: '系统级参数错误',
    API_10102_SIGNATURE_ERROR: '签名值错误',
}
