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
import plistlib
from PIL import Image
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from base.exceptions import ParamErrorException
from api.settings import MEDIA_ROOT
import os
from django.db.models import Q
from config.models import Admin_Operation
from quiz.models import Record
from base import code
from users.models import DailyLog, UserMessage, UserCoinLock, UserPresentation, User, Coin, UserCoin
from console.models import Address
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


def random_invitation_code(length=5):
    """
    生成指定长度随机字符串
    :param length: 随机数长度
    :return:
    """
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    char_length = len(chars) - 1
    random = Random()

    random_str = ''
    for i in range(length):
        random_str += chars[random.randint(0, char_length)]
    user_list = User.objects.filter(invitation_code=random_str).count()
    if user_list == 0:
        return random_str
    return random_invitation_code()


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
    try:
        user_sign = DailyLog.objects.get(user_id=user_id)
    except DailyLog.DoesNotExist:
        return 0

    sign_date = user_sign.sign_date.strftime("%Y%m%d%H%M%S")
    today = datetime.date.today()
    today_time = today.strftime("%Y%m%d%H%M%S")
    if int(sign_date) >= int(today_time):
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
    item = UserPresentation.objects.filter(user_id=user, coin_id=coin, status=0).aggregate(Sum('amount'))
    rest = item['amount__sum']
    if rest == None:
        rest = 0
    else:
        rest = item['amount__sum']
    return rest


def resize_img(image, dst_w=0, dst_h=0, qua=95):
    """
    :param file1: 图像文件
    :param file2: 保存文件
    :param dst_w: 需生成的图像宽(默认则不改变)
    :param dst_h: 需生成的图像高(默认则不改变)
    :param qua: 图片生成质量
    :return:
    """

    img = Image.open(image)
    ori_w, ori_h = img.size
    widthRatio = heightRatio = None
    ratio = 1
    if (ori_w and ori_w > dst_w) or (ori_h and ori_h > dst_h):
        if dst_w and ori_w > dst_w:
            widthRatio = float(dst_w) / ori_w  # 正确获取小数的方式
        if dst_h and ori_h > dst_h:
            heightRatio = float(dst_h) / ori_h
        if widthRatio and heightRatio:
            if widthRatio < heightRatio:
                ratio = widthRatio
            else:
                ratio = heightRatio
        if widthRatio and not heightRatio:
            ratio = widthRatio
        if heightRatio and not widthRatio:
            ratio = heightRatio
        newWidth = int(ori_w * ratio)
        newHeight = int(ori_h * ratio)
    else:
        newWidth = ori_w
        newHeight = ori_h
    img.resize((newWidth, newHeight), Image.ANTIALIAS).save(image, quality=qua)


# 去掉decimal类型数值后面的0
def normalize_fraction(d, b):
    d = Decimal(str(d))
    dd = round(d, b)
    normalized = dd.normalize()
    sign, digit, exponent = normalized.as_tuple()
    return normalized if exponent <= 0 else normalized.quantize(1)


def genarate_plist(version, file_path):
    """
    生成IOS plist文件
    :param version: 版本号
    :param filepath: ipa文件保存路径
    :return:
    """
    temp_x = {'items': [{'assets': [{'kind': 'software-package',
                                     'url': file_path}],
                         'metadata': {'bundle-identifier': 'iPhone Developer: shenghong liu (K7AC5W2PGD)',
                                      'bundle-version': version,
                                      'kind': 'software',
                                      'title': u'\u8d85\u7ea7\u6e38\u620f'}}]}
    save_file = os.path.join(MEDIA_ROOT, 'apps/IOS', 'version_%s_IOS.plist' % version)
    with open(save_file, 'wb') as fp:
        plistlib.dump(temp_x, fp)


def coin_initialization(user_id, coin_id):
    coin_info = Coin.objects.get(pk=coin_id)
    is_usercoin = UserCoin.objects.filter(coin_id=coin_id, user_id=user_id)
    user = User.objects.get(pk=user_id)
    if len(is_usercoin) <= 0:                 # 是否有余额表记录
        if coin_info.is_eth_erc20:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).first()
            else:
                address = Address.objects.filter(user=0, coin_id=Coin.ETH).first()
                address.user = user.pk
                address.save()
        else:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).first()
            else:
                address = Address.objects.filter(user=0, coin_id=Coin.BTC).first()
                address.user = user.pk
                address.save()

        user_coin = UserCoin()
        user_coin.coin = coin_info
        user_coin.user = user
        user_coin.address = address.address
        user_coin.save()
    is_address = UserCoin.objects.filter(~Q(address=''), coin_id=coin_id, user_id=user_id).count()
    if is_address == 0:
        if coin_info.is_eth_erc20:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).first()
            else:
                address = Address.objects.filter(user=0, coin_id=Coin.ETH).first()
                address.user = user.pk
                address.save()
        else:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).first()
            else:
                address = Address.objects.filter(user=0, coin_id=Coin.BTC).first()
                address.user = user.pk
                address.save()
        address.user = user
        address.save()
        user_coin = UserCoin.objects.get(coin_id=coin_id, user_id=user_id)
        user_coin.address = address.address
        user_coin.save()
