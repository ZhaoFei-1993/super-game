# 删除图形验证码
import os
from local_settings import all_settings
import MySQLdb
from datetime import datetime, date, timedelta


def getDatetimeToday():
    t = date.today()  # date类型
    dt = datetime.strptime(str(t), '%Y-%m-%d')  # date转str再转datetime
    return dt


def getDatetimeYesterday():
    today = getDatetimeToday()  # datetime类型当前日期
    yesterday = today + timedelta(days=-1)  # 减去一天
    return yesterday


def delete_capcha():
    print(os.listdir('./captcha_img'))


if __name__ == '__main__':
    delete_capcha()
    print(getDatetimeYesterday())
