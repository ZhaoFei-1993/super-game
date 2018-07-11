"""
auth: lijun
function:  删除图形验证码脚本，可用crontab定期执行;接口程序中只对有调用验证接口的图片进行删除，会遗留没有验证的图片
date： 2018.7.10
"""
import os
import MySQLdb
from datetime import datetime, date, timedelta
from local_settings.all_settings import DB


def getDatetimeToday():
    t = date.today()  # date类型
    dt = datetime.strptime(str(t), '%Y-%m-%d')  # date转str再转datetime
    return dt


def getDatetimeYesterday():
    today = getDatetimeToday()  # datetime类型当前日期
    yesterday = today - timedelta(days=0.5)  # 减去半天
    return yesterday


def get_db():
    db = DB['NAME']
    host = DB['HOST']
    user = DB['USER']
    password = DB['PASSWORD']
    con = MySQLdb.connect(host, user, password, db, charset='utf8')
    return con


def delete_capcha():  # 删除半天之前未删除的图形验证码,并对数据库进行清理
    yesterday = getDatetimeYesterday()
    con = get_db()
    cursor = con.cursor()
    cursor.execute('select name from utils_codemodel where status=0 and created_at<"%s"' % (str(yesterday, )))
    data = cursor.fetchall()
    for item in data:
        try:
            os.remove(os.path.join('./captcha_img', item[0])) # 删除图片
            print('成功删除图片:%s' % item[0])
        except:
            pass
        cursor.execute('delete from utils_codemodel where name="%s"' % item[0])
        print('清除图片sql数据：',item[0])
        con.commit()
    con.close()


if __name__ == '__main__':
    delete_capcha()
