# 删除图形验证码
import os
from local_settings import all_settings
import MySQLdb
from datetime import datetime, date, timedelta
from local_settings.all_settings import DB

def getDatetimeToday():
    t = date.today()  # date类型
    dt = datetime.strptime(str(t), '%Y-%m-%d')  # date转str再转datetime
    return dt

def getDatetimeYesterday():
    today = getDatetimeToday()  # datetime类型当前日期
    yesterday = today + timedelta(days=-1)  # 减去一天
    return yesterday

def get_db():
    db = DB['NAME']
    host = DB['HOST']
    user = DB['USER']
    password = DB['PASSWORD']
    con = MySQLdb.connect(host,user,password,db,charset='utf8')
    return con

def delete_capcha():
    con = get_db()
    cursor = con.cursor()
    cursor.execute('select * from utils_codemodel')
    data = cursor.fetchall()
    print(data)
    con.close()


if __name__ == '__main__':
    delete_capcha()
    print(getDatetimeYesterday())
