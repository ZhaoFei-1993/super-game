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
import decimal
from PIL import Image
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.db.models import Sum, Q
from base import code as error_code
import hashlib
from chat.models import Club
from base.exceptions import ParamErrorException
from api.settings import MEDIA_ROOT, MEDIA_DOMAIN_HOST
import os
from config.models import Admin_Operation
from quiz.models import Record
from base import code
from users.models import DailyLog, UserMessage, UserCoinLock, UserPresentation, User, Coin, UserCoin
from console.models import Address
import reversion
from wc_auth.functions import save_operation
from django.db import connection
from PIL import Image, ImageDraw, ImageFont
import random
from utils.cache import get_cache, set_cache
from dragon_tiger.models import Showroad, Bigroad, Psthway, Bigeyeroad, Roach


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
    user_message = UserMessage.objects.filter(user_id=user_id, status=0).count()
    if user_message > 0:
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
                         'metadata': {'bundle-identifier': 'com.appvv.guessball',
                                      'bundle-version': version,
                                      'kind': 'software',
                                      'title': u'\u8d85\u7ea7\u6e38\u620f'}}]}
    now_time = datetime.datetime.now().strftime('%Y%m%d%H%M')
    file = '%s_version_%s_IOS.plist' % (now_time, version)
    save_file = os.path.join(MEDIA_ROOT, 'apps/IOS', file)
    with open(save_file, 'wb') as fp:
        plistlib.dump(temp_x, fp)
    file_url = os.path.join(MEDIA_DOMAIN_HOST, 'apps/IOS', file)
    return file_url


@transaction.atomic()
def coin_initialization(user_id, coin_id):
    coin_info = Coin.objects.get(pk=coin_id)
    is_usercoin = UserCoin.objects.filter(coin_id=coin_id, user_id=user_id).count()
    user = User.objects.get(pk=user_id)
    if is_usercoin <= 0:  # 是否有余额表记录
        if coin_info.is_eth_erc20:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).first()
            else:
                address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.ETH).first()
                address.user = user.pk
                address.save()
        else:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id,
                                                       coin__is_eth_erc20=False).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).first()
            else:
                address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.BTC).first()
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
                address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.ETH).first()
                address.user = user_id
                address.save()
        else:
            user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id,
                                                       coin__is_eth_erc20=False).count()
            if user_coin_number != 0:
                address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=False).first()
            else:
                address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.BTC).first()
                address.user = user_id
                address.save()
        user_coin = UserCoin.objects.get(coin_id=coin_id, user_id=user_id)
        user_coin.address = address.address
        user_coin.save()


def language_switch(language, parameter):
    """
    语言处理
    """
    if language == 'en':
        parameter = str(parameter) + '_' + language
    return parameter


#
# def language(language, parameter):
#     """
#     语言
#     """
#     parameter = parameter
#     if language == 'en':
#         parameter = parameter + '_' + language
#     return parameter


def get_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql, None)
        dt_all = cursor.fetchall()
    return dt_all


#
# @transaction.atomic()
# def gsg_coin_initialization(user_id, coin_id):
#     coin_info = Coin.objects.get(pk=coin_id)
#     user = User.objects.get(pk=user_id)
#     user_coin_number = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).count()
#     if user_coin_number != 0:
#         address = UserCoin.objects.filter(~Q(address=''), user_id=user_id, coin__is_eth_erc20=True).first()
#     else:
#         address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.ETH).first()
#         address.user = user.pk
#         address.save()
#     gsg_count = UserCoin.objects.filter(user_id=user_id, coin_id=6).count()
#     if gsg_count == 0:
#         user_coin = UserCoin()
#         user_coin.coin = coin_info
#         user_coin.user = user
#         user_coin.balance = Decimal(user.integral)
#         user_coin.address = address.address
#         user_coin.save()
#     else:
#         user_coin = UserCoin.objects.get(user_id=user_id, coin_id=6)
#         user_coin.address = address.address
#         user_coin.save()
#     return user_coin

class RandomChar(object):
    """汉字生成类"""

    @staticmethod
    def Unicode():
        # val = random.randint(0x4E00, 0x9FBF)
        # return unichr(val)
        return "你好"

    @staticmethod
    def GB2312():
        head = random.randint(0xb0, 0xf7)
        body = random.randint(0xa1, 0xf9)  # 在head区号为55的那一块最后5个汉字是乱码,为了方便缩减下范围
        val = f'{head:x}{body:x}'
        str = bytes.fromhex(val).decode('gb2312')
        return str


class ImageChar(object):
    """验证码图片生成"""

    # SAVE_PATH = os.path.join(os.getcwd(), 'utils/captcha_img')

    def __init__(self, fontColor=(0, 0, 0),
                 size=(300, 200),
                 fontPath='./utils/simsun.ttc',
                 bgColor=(255, 255, 255),
                 fontSize=20):
        self.size = size
        self.fontPath = fontPath
        self.bgColor = bgColor
        self.fontSize = fontSize
        self.fontColor = fontColor
        self.font = ImageFont.truetype(self.fontPath, self.fontSize)
        self.image = Image.new('RGB', size, bgColor)

    def rotate(self):
        self.image.rotate(random.randint(0, 90), expand=0)

    def drawText(self, pos, txt, fill):
        draw = ImageDraw.Draw(self.image)
        draw.text(pos, txt, font=self.font, fill=fill)

    def randRGB(self):
        return (random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100))

    def lineRGB(self):
        return (random.randint(150, 255),
                random.randint(150, 255),
                random.randint(150, 255))

    def randPoint(self):
        (width, height) = self.size
        return (random.randint(0, width), random.randint(0, height))

    def randLine(self, num):
        draw = ImageDraw.Draw(self.image)
        for i in range(0, num):
            draw.line([self.randPoint(), self.randPoint()], self.lineRGB())

    def randCH_or_EN(self, num=6, style='zh', select=4):  # 总共生成6个字，选取4个字
        co_list = []  # 坐标列表，存储已经生成的坐标保证不重叠
        char_list = []  # 汉字列表,存储汉字保证不重复
        res_co_list = []  # 存储返回结果的4个坐标
        res_char_list = []  # 存储返回结果的4个汉字
        for i in range(1, num + 1):
            if style == 'zh':  # 中文
                while True:
                    try:
                        char = RandomChar().GB2312()  # 随机生成中文字符串
                        if char not in char_list:
                            char_list.append(char)
                            if i <= select:
                                res_char_list.append(char)
                            break
                    except Exception as e:
                        pass
            else:
                en_list = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
                while True:
                    char = random.sample(en_list, 1)[0]  # 随机生成中文字符串
                    if char not in char_list:
                        char_list.append(char)
                        if i <= select:
                            res_char_list.append(char)
                        break

            while True:
                x = random.randint(0, self.size[0] - self.fontSize)  # 生成左顶点的横坐标
                y = random.randint(0, self.size[1] - self.fontSize)  # 生成左顶点的纵坐标
                x_right = x + self.fontSize  # 计算横坐标最右值
                y_foot = y + self.fontSize  # 计算纵坐标的最右值
                if not co_list:  # 列表为空直接存入坐标范围
                    co_list.append([[x, x_right], [y, y_foot]])
                    res_co_list.append([[x, x_right], [y, y_foot]])
                    break
                else:  # 若坐标不为空则判断生成的中文是否有重叠，重叠则继续循环
                    for co in co_list:
                        if self.judge_co(co[0], [x, x_right]) and self.judge_co(co[1], [y,
                                                                                        y_foot]):  # 若横纵坐标存在没有交集，则成功生成汉字,跳出两层循环，否则继续循环直到找到合适的坐标
                            break
                    else:
                        co_list.append([[x, x_right], [y, y_foot]])
                        if i <= select:
                            res_co_list.append([[x, x_right], [y, y_foot]])
                        break

            self.drawText((x, y), char, self.randRGB())
            # self.rotate()
        self.randLine(20)
        return res_char_list, res_co_list

    def judge_co(self, list1, list2):
        """判断文字区间是否有重叠"""
        if list1[1] < list2[0] or list2[1] < list1[0]:  # 没重叠
            return False
        else:  # 重叠
            return True

    def save(self, path):
        self.image.save(path)


def string_to_list(str):
    """将x,y|x,y|x,y|x,y格式的字符串转化成列表"""
    lists = str.split('|')
    try:
        res = [[int(i.split(',')[0]), int(i.split(',')[1])] for i in lists if len(i.split(',')) == 2]
    except:
        return None

    if len(res) == 4:
        return res
    else:
        return None


def message_code(length=6, mode='digit'):
    """
    随机短信验证码,代替原先从外部导入的sms
    :param length:  验证码长度，默认6位 
    :param mode:    模式：默认纯数字，后期扩展字母数字混合
    :return: 
    """
    rand_code = []
    for i in range(0, length):
        rand_code.append(str(random.randint(0, 10)))

    codes = ''.join(rand_code)
    return codes[0:length]


def guess_is_seal(info):
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    begin_at = info.rotary_header_time.astimezone(pytz.timezone(settings.TIME_ZONE))
    begin_at = time.mktime(begin_at.timetuple())
    start = int(begin_at)
    timeArray = time.localtime(start)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    if nowtime >= otherStyleTime:  # 是否已封盘
        info.is_seal == 1
        info.save()
    return info.is_seal


def effect_user():
    sql = "select a.id from users_user a"
    sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
    sql += " where b.count <=3 "
    sql += " and is_robot=0 and is_block=0"
    dt_all = list(get_sql(sql))

    sql = "select distinct(user_id) from users_userrecharge"
    dt_recharge = list(get_sql(sql))

    dt_all = list(set(dt_all + dt_recharge))
    dd = []
    for x in dt_all:
        dd.append((x[0]))
    return dd


def number_time_judgment():
    day = datetime.datetime.now().strftime('%Y-%m-%d')
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time_key = "INITIAL_ONLINE_TIME_NOW_" + str(day)
    initial_online_user_time = get_cache(time_key)
    # if initial_online_user_time == None or initial_online_user_time == '':
    #     key = 1
    # else:
    # time_one = initial_online_user_time['time_one']
    time_one = day + str(initial_online_user_time[0]['time_one'])
    time_two = day + str(initial_online_user_time[0]['time_two'])
    time_three = day + str(initial_online_user_time[0]['time_three'])
    time_four = day + str(initial_online_user_time[0]['time_four'])
    time_five = day + str(initial_online_user_time[0]['time_five'])
    time_six = day + str(initial_online_user_time[0]['time_six'])
    time_seven = day + str(initial_online_user_time[0]['time_seven'])
    time_eight = day + str(initial_online_user_time[0]['time_eight'])
    # time_nine = str(day) + str(initial_online_user_time['time_nine'])
    # time_ten = str(day) + str(initial_online_user_time['time_ten'])
    if nowtime >= time_one and nowtime <= time_two:
        key = 1
    elif nowtime >= time_three and nowtime <= time_four:
        key = 2
    elif nowtime >= time_five and nowtime <= time_six:
        key = 3
    elif nowtime >= time_seven and nowtime <= time_eight:
        key = 4
    else:
        key = 5
    return key


def make_insert_sql(table_name, values):
    """
    组装插入的SQL语句
    :param table_name:  表名
    :param values:      字段 => 值
    :usage: table_name=mytable, values=[{"a": "hello", "b": "world"}, {"a": "good", "b": "day"}]
            ==> INSERT INTO mytable (`a`, `b`) VALUES ("hello", "world"), ("good", "day")
    :return:
    """
    if len(values) == 0:
        return False

    field = '`' + '`,`'.join(values[0].keys()) + '`'
    arr_values = []
    for value in values:
        arr_values.append('(\'' + '\',\''.join(list(value.values())) + '\')')

    return 'INSERT INTO ' + table_name + ' (' + field + ') VALUES ' + ','.join(arr_values)


def make_batch_update_sql(table_name, values, update):
    """
    组装批量更新的SQL语句
    :param table_name:  表名
    :param values:      字段 => 值
    :return: INSERT INTO `tbl` (`a`, `b`, `c`) VALUES (2, 3, 123) ON DUPLICATE KEY UPDATE updates;
    """
    if len(values) == 0:
        return False

    field = '`' + '`,`'.join(values[0].keys()) + '`'
    arr_values = []
    for value in values:
        arr_values.append('(\'' + '\',\''.join(list(value.values())) + '\')')

    mysql_update = ' ON DUPLICATE KEY UPDATE ' + update
    return 'INSERT INTO ' + table_name + ' (' + field + ') VALUES ' + ','.join(arr_values) + mysql_update


def get_club_info():
    """
        从缓存读取club_info
        :return: 俱乐部信息字典;
    """
    cache_club_key = 'club_info'
    cache_club_value = get_cache(cache_club_key)
    if cache_club_value is None:
        set_cache(cache_club_key, {})
        for club in Club.objects.all():
            cache_club_value_origin = get_cache(cache_club_key)
            cache_club_value = {
                club.id: {
                    'coin_id': club.coin_id, 'club_name': club.room_title,
                    'club_name_en': club.room_title_en, 'coin_name': club.room_title.replace('俱乐部', ''),
                    'coin_accuracy': club.coin.coin_accuracy,
                }
            }
            cache_club_value_origin.update(cache_club_value)
            set_cache(cache_club_key, cache_club_value_origin)
            cache_club_value = get_cache(cache_club_key)
    return cache_club_value


# 将科学计数法转换为字符串
def sc2str(sc, digit):
    vv = str('%.' + str(digit) + 'f') % Decimal(str(sc))
    return vv


def float_to_str(f, x=5):
    ctx = decimal.Context()
    x += 3
    ctx.prec = x
    d1 = ctx.create_decimal(repr(f))
    numbers = format(d1, 'f')
    number = numbers[0:-2]
    return number


def obtain_token(menu, game):
    appid = '58000000'  # 获取token需要参数Appid
    appsecret = '92e56d8195a9dd45a9b90aacf82886b1'  # 获取token需要参数Secret
    times = int(time.time())  # 获取token需要参数time
    array = {'appid': '58000000', 'menu': menu, 'game': game}  # 全部
    m = hashlib.md5()  # 创建md5对象
    hash_str = str(times) + appid + appsecret
    hash_str = hash_str.encode('utf-8')
    m.update(hash_str)
    token = m.hexdigest()
    array['token'] = token
    list = ""
    for key in array:
        value = array[key]
        list += str(key) + str(value)
    list += appsecret
    list = list.encode('utf-8')
    sign = hashlib.sha1(list)
    sign = sign.hexdigest()
    sign = sign.upper()
    array['sign'] = sign
    return array


def ludan_save(messages, boots):
    if messages["round"]["ludan"] != False:

        showroad_number = Showroad.objects.filter(boots_id=boots.id).count()
        if "showRoad" in messages["round"]["ludan"]:
            if messages["round"]["ludan"]["showRoad"]["previous_res"] != None:
                is_showroad_number = len(messages["round"]["ludan"]["showRoad"]["show_location"])
                if int(is_showroad_number) > int(showroad_number):
                    s = 1
                    for i in messages["round"]["ludan"]["showRoad"]["show_location"]:
                        if s > showroad_number:
                            showroad = Showroad()
                            showroad.boots = boots
                            if i["result"] == "banker":
                                result_show = 1
                            elif i["result"] == "player":
                                result_show = 2
                            else:
                                result_show = 3
                            showroad.result_show = result_show
                            showroad.order_show = s
                            showroad.show_x_show = i["show_x"]
                            showroad.show_y_show = i["show_y"]
                            if i["pair"] == "bankerPair":
                                pair = 1
                            elif i["pair"] == "playerPair":
                                pair = 2
                            elif i["pair"] == "bothPair":
                                pair = 3
                            else:
                                pair = 0
                            showroad.pair = pair
                            showroad.save()
                            print("结果路图入库成功============================", s, "条")
                        s += 1
                else:
                    print("--------结果图早已入库--------")
            else:
                print("--------结果图数据为空--------")
        else:
            print("--------结果图暂无数据--------")

        bigroad_number = Bigroad.objects.filter(boots_id=boots.id).count()
        if "bigRoad" in messages["round"]["ludan"]:
            if messages["round"]["ludan"]["bigRoad"]["previous_res"] != None:
                is_bigroad_number = len(messages["round"]["ludan"]["bigRoad"]["show_location"])
                if int(is_bigroad_number) > int(bigroad_number):
                    b = 1
                    for i in messages["round"]["ludan"]["bigRoad"]["show_location"]:
                        if b > bigroad_number:
                            bigroad = Bigroad()
                            bigroad.boots = boots
                            if i["result"] == "banker":
                                result_big = 1
                            else:
                                result_big = 2
                            if b == 1 and int(i["tie_num"]) == 1:
                                result_big = 3
                            bigroad.result_big = result_big
                            bigroad.order_big = b
                            bigroad.show_x_big = i["show_x"]
                            bigroad.show_y_big = i["show_y"]
                            if i["tie_num"] != 0:
                                bigroad.tie_num = 1
                            bigroad.save()
                            print("大路图入库成功============================", b, "条")
                        b += 1
                else:
                    b_test = 1
                    for i in messages["round"]["ludan"]["bigRoad"]["show_location"]:
                        if b_test == bigroad_number:
                            if i["tie_num"] != 0:
                                bigroad = Bigroad.objects.filter(boots_id=boots.id).first()
                                bigroad.tie_num = 1
                                bigroad.save()
                            print("------------改变大路图最后一条数据，确保出现和的录入------------")
                        b_test += 1
                    print("--------大路图早已入库--------")
            else:
                print("--------大路图数据为空--------")
        else:
            print("--------大路图暂无数据--------")

        bigeyeroad_number = Bigeyeroad.objects.filter(boots_id=boots.id).count()
        if "bigEyeRoad" in messages["round"]["ludan"]:
            if messages["round"]["ludan"]["bigEyeRoad"]["previous_res"] != None:
                is_bigeyeroad_number = len(messages["round"]["ludan"]["bigEyeRoad"]["show_location"])
                if int(is_bigeyeroad_number) > int(bigeyeroad_number):
                    by = 1
                    for i in messages["round"]["ludan"]["bigEyeRoad"]["show_location"]:
                        if by > bigeyeroad_number:
                            bigeyeroad = Bigeyeroad()
                            bigeyeroad.boots = boots
                            if i["result"] == "banker":
                                result_big_eye = 1
                            else:
                                result_big_eye = 2
                            bigeyeroad.result_big_eye = result_big_eye
                            bigeyeroad.order_big_eye = by
                            bigeyeroad.show_x_big_eye = i["show_x"]
                            bigeyeroad.show_y_big_eye = i["show_y"]
                            bigeyeroad.save()
                            print("大眼路图入库成功============================", by, "条")
                        by += 1
                else:
                    print("--------大眼路图早已入库--------")
            else:
                print("--------大眼路图数据为空--------")
        else:
            print("--------大眼路图暂无数据--------")

        psthway_number = Psthway.objects.filter(boots_id=boots.id).count()
        if "pathway" in messages["round"]["ludan"]:
            if messages["round"]["ludan"]["pathway"]["previous_res"] != None:
                is_psthway_number = len(messages["round"]["ludan"]["pathway"]["show_location"])
                if int(is_psthway_number) > int(psthway_number):
                    p = 1
                    for i in messages["round"]["ludan"]["pathway"]["show_location"]:
                        if p > psthway_number:
                            psthway = Psthway()
                            psthway.boots = boots
                            if i["result"] == "banker":
                                result_psthway = 1
                            else:
                                result_psthway = 2
                            psthway.result_psthway = result_psthway
                            psthway.order_psthway = p
                            psthway.show_x_psthway = i["show_x"]
                            psthway.show_y_psthway = i["show_y"]
                            psthway.save()
                            print("小路图入库成功============================", p, "条")
                        p += 1
                else:
                    print("--------小路图早已入库--------")
            else:
                print("--------小路图数据为空--------")
        else:
            print("--------小路图暂无数据--------")

        roach_number = Roach.objects.filter(boots_id=boots.id).count()
        if "roach" in messages["round"]["ludan"]:
            if messages["round"]["ludan"]["roach"]["previous_res"] != None:
                is_roach_number = len(messages["round"]["ludan"]["roach"]["show_location"])
                if int(is_roach_number) > int(roach_number):
                    rn = 1
                    for i in messages["round"]["ludan"]["roach"]["show_location"]:
                        if rn > roach_number:
                            roach = Roach()
                            roach.boots = boots
                            if i["result"] == "banker":
                                result_roach = 1
                            else:
                                result_roach = 2
                            roach.result_roach = result_roach
                            roach.order_roach = rn
                            roach.show_x_roach = i["show_x"]
                            roach.show_y_roach = i["show_y"]
                            roach.save()
                            print("珠盘路图入库成功============================", rn, "条")
                        rn += 1
                else:
                    print("--------珠盘路图早已入库--------")
            else:
                print("--------珠盘路数据为空--------")
        else:
            print("--------珠盘路暂无数据--------")
