# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score
import hashlib
import time

# m = hashlib.md5()  # 创建md5对象
# m.update('abcdefg')  # 生成加密串，其中password是要加密的字符串
# print
# m.hexdigest()


class Encryption(BaseCommand):
    appid = '58000000'      #你的Appid
    appsecret = '92e56d8195a9dd45a9b90aacf82886b1'     #你的Secret
    url = 'http://api.wt123.co/service'        #API请求地址 | 测试阶段地址
    time = int(time.time())
    print("time================================", time)
    m = hashlib.md5()  # 创建md5对象
    hash_str = str(time)+appid+appsecret
    hash_str = hash_str.encode('utf-8')
    m.update(hash_str)
    token = m.hexdigest()
    print("$token==============================", token)


#     $token = md5(time().$appid.$appsecret);
#     $array['token'] = $token;
#     // 1.
#     对加密数组进行字典排序
#     foreach($array as $key = > $value){
#     $arr[$key] = $key;
#     }
#     // 2.
#     将Key和Value拼接
#     $str = "";
#     foreach($arr as $k = > $v) {
#     $str = $str.$arr[$k].$array[$v];
#     }
#     // 3.
#     通过sha1加密并转化为大写
#     // 4.
#     大写获得签名
#     $restr = $str.$appsecret;
#     $sign = strtoupper(sha1($restr));
#     $array['sign'] = $sign;
#     return $array;
#
# }
#
# $appid = '58000000'; // 你的Appid
# $appsecret = '92e56d8195a9dd45a9b90aacf82886b1'; // 你的Secret
# $url = 'http://api.wt123.co/service'; // API请求地址 | 测试阶段地址
# ? >