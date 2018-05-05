# -*- coding: UTF-8 -*-
"""
@author: h3l
@contact: rexlin0624@gmail.com
@file: functions.py
@time: 2017/2/21 11:35
"""
from random import Random
import time
import pytz
import datetime
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from base.exceptions import ParamErrorException
from django.db.models import Q
from wc_auth.models import Admin_Operation
from quiz.models import Record
from base import code
from users.models import DailyLog, UserMessage, UserCoinLock, UserPresentation
import reversion
from wc_auth.functions import save_operation


def random_string(length=16):
    """
    生成指定长度随机字符串
    :param length: 随机数长度
    :return: 
    """
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    char_length = len(chars) - 1
    random = Random()

    random_str = ''
    for i in range(length):
        random_str += chars[random.randint(0, char_length)]
    return random_str


def random_salt(length=12):
    """
    随机salt值
    :param length: 
    :return: 
    """
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789~!@#$%^&*()-'
    char_length = len(chars) - 1
    random = Random()

    random_str = ''
    for i in range(length):
        random_str += chars[random.randint(0, char_length)]
    return random_str


def convert_localtime(value):
    """
    UTC转换为当前时间
    :param value:
    :return:
    """
    local_tz = pytz.timezone(settings.TIME_ZONE)

    return value.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')


def value_judge(request, *args):  # 查看客户端有没有漏传字段
    for i in args:
        if i not in request.data or request.data.get(i) == '' or request.data.get(i) is None:
            return 0
    return 1


def surplus_date(end_date):
    """
    下注截止时间计算
    """
    end_date = end_date.astimezone(pytz.timezone(settings.TIME_ZONE))
    end_date = time.mktime(end_date.timetuple())
    nowtime = datetime.datetime.now()
    now = nowtime.astimezone(pytz.timezone(settings.TIME_ZONE))
    now = time.mktime(now.timetuple())
    surplus = end_date - now
    if surplus > 0:
        return int(surplus)
    else:
        return 0


def reasonable_time(end_date):  # 查看客户端传过来的题目结束时间是否合理
    # 将其转换为时间数组
    timeArray = time.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    # 转换为时间戳
    timeStamp = int(time.mktime(timeArray))

    nowtime = datetime.datetime.now()
    now = nowtime.astimezone(pytz.timezone(settings.TIME_ZONE))
    now = time.mktime(now.timetuple())
    surplus = timeStamp - now
    if surplus > 0:
        return int(surplus)
    else:
        return 0


def value_judge(request, *args):
    # 查看客户端有没有漏传字段
    for i in args:
        if i not in request.data or request.data.get(i) == '' or request.data.get(i) is None:
            return 0
    return 1


def sign_confirmation(user_id):
    # 是否签到
    user_sign = DailyLog.objects.get(user_id=user_id)
    sign_date = user_sign.sign_date.strftime("%Y%m%d%H%M%S")
    today = datetime.date.today()
    today_time = today.strftime("%Y%m%d%H%M%S")
    if int(sign_date) > int(today_time):
        is_sign = 1
    elif int(sign_date) == int(today_time):
        is_sign = 1
    else:
        is_sign = 0
    return is_sign


def message_hints(user_id):
    # 是否有未读信息
    user_message = UserMessage.objects.filter(user_id=user_id, status=0)
    len(user_message)
    if len(user_message) > 0:
        is_message = 1
    else:
        is_message = 0
    return is_message


def message_sign(user_id, type):
    #  公共消息标记
    usermessage = UserMessage.objects.filter(user_id=user_id, status=0)
    sign = 0
    for list in usermessage:
        if int(list.message.type) == type:
            sign = 1
    return sign


def amount(user_id):
    usercoin = UserCoinLock.objects.filter(user_id=user_id)
    coin = 0
    if len(usercoin) == 0:
        return coin
    for list in usercoin:
        if list.end_time < list.created_at:
            continue
        elif list.end_time == list.created_at:
            continue
        else:
            coin += list.amount
    return coin


def surplus_date(end_date):
    """
    下注截止时间计算
    """
    end_date = end_date.astimezone(pytz.timezone(settings.TIME_ZONE))
    end_date = time.mktime(end_date.timetuple())
    nowtime = datetime.datetime.now()
    now = nowtime.astimezone(pytz.timezone(settings.TIME_ZONE))
    now = time.mktime(now.timetuple())
    surplus = end_date - now
    if surplus > 0:
        return int(surplus)
    else:
        return 0


# def win_ratio(user_id):
#     """
#     获取自己胜录
#     :param user_id:
#     :return:
#     """
#     total_count = Record.objects.filter(~Q(earn_coin='0'), user_id=user_id).count()
#     win_count = Record.objects.filter(user_id=user_id, earn_coin__gt=0).count()
#     if total_count == 0 or win_count == 0:
#         win_ratio = "0%"
#     else:
#         record_count = round(win_count / total_count * 100, 2)
#         win_ratio = str(record_count) + "%"
#     return win_ratio


def reversion_Decorator(func):
    """
    各种request请求(不包含OPTIONS, GET ,HEAD)函数装饰器,记录各种操作请求
    """

    def wrapper(self, request, *args, **kwargs):
        if request.method in ['HEAD', 'OPTIONS', 'GET']:
            raise ParamErrorException(code.API_405_WAGER_PARAMETER)
        with reversion.create_revision(atomic=True):
            result = func(self, request, *args, **kwargs)
            reversion.set_user(request.user)
            reversion.set_comment(request.method)
        save_operation(request)
        return result

    return wrapper


def amount_presentation(user, coin):
    coin = UserPresentation.objects.filter(user_id=user, coin_id=coin, status=0).aggregate(Sum('amount'))
    return coin['amount__sum']
