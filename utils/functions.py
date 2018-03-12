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
from django.conf import settings
from django.db.models import Q

from quiz.models import Record
from users.models import DailyLog, UserMessage, UserCoinLock


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
    sign_date = user_sign.sign_date
    tmp = time.strftime("%Y%m%d")
    if sign_date > int(tmp):
        is_sign = 1
    elif sign_date == int(tmp):
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


def win_ratio(user_id):
    """
    获取自己胜录
    :param user_id:
    :return:
    """
    total_count = Record.objects.filter(~Q(earn_coin='0'), user_id=user_id).count()
    win_count = Record.objects.filter(user_id=user_id, earn_coin__gt=0).count()
    if total_count == 0 or win_count == 0:
        win_ratio = "0%"
    else:
        record_count = round(win_count / total_count * 100, 2)
        win_ratio = str(record_count) + "%"
    return win_ratio



# def calculation(liat,lists):
#     if liat == lists:
#         lists = ""
#     else:
#         liat = lists
#     return lists