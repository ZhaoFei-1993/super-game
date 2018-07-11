# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests

url = 'https://1680660.com/smallSix/findSmallSixHistory.do'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

color_dic = {
    '红': ['01', '02', '07', '08', '12', '13', '18', '19', '23', '24', '29', '30', '34', '35', '40', '45', '46'],
    '蓝': ['03', '04', '09', '10', '14', '15', '20', '25', '26', '31', '36', '37', '41', '42', '47', '48'],
    '绿': ['05', '06', '11', '16', '17', '21', '22', '27', '28', '32', '33', '38', '39', '43', '44', '49'],
}
chinese_zodiac_dic = {
    '狗': ['01', '13', '25', '37', '49'],
    '猪': ['12', '24', '36', '48'],
    '鼠': ['11', '23', '35', '47'],
    '牛': ['10', '22', '34', '46'],
    '虎': ['09', '21', '33', '45'],
    '兔': ['08', '20', '32', '44'],
    '龙': ['07', '19', '31', '43'],
    '蛇': ['06', '18', '30', '42'],
    '马': ['05', '17', '29', '41'],
    '羊': ['04', '16', '28', '40'],
    '猴': ['03', '15', '27', '39'],
    '鸡': ['02', '14', '26', '38'],
}
five_property_dic = {
    '金': ['04', '05', '18', '19', '26', '27', '34', '35', '48', '49'],
    '木': ['01', '08', '09', '16', '17', '30', '31', '38', '39', '46', '47'],
    '水': ['06', '07', '14', '15', '22', '23', '36', '37', '44', '45'],
    '火': ['02', '03', '10', '11', '24', '25', '32', '33', '40', '41'],
    '土': ['12', '13', '20', '21', '28', '29', '42', '43'],
}


def mark_six_result(pre_draw_code_list):
    # 码数
    code_list = []
    # 色波
    color_list = []
    # 生肖
    chinese_zodiac_list = []
    # 五行
    five_property_list = []

    for code in pre_draw_code_list:
        if len(code) == 1:
            code = '0' + code
        code_list.append(code)

        for key, value in color_dic.items():
            if code in value:
                color_list.append(key)

        for key, value in chinese_zodiac_dic.items():
            if code in value:
                chinese_zodiac_list.append(key)

        for key, value in five_property_dic.items():
            if code in value:
                five_property_list.append(key)

    print(code_list, color_list, chinese_zodiac_list, five_property_list, sep='\n')
    print('----------------------------------------------------------------------')


class Command(BaseCommand):
    help = "mark six result"

    def handle(self, *args, **options):
        proxies = {
            'https': '127.0.0.1:8123',
        }
        data = {
            'type': 1,
            'year': 2018,
        }

        response = requests.post(url, data=data, headers=headers)
        body_list = response.json()['result']['data']['bodyList'][0]

        pre_draw_date = body_list['preDrawDate']
        issue = body_list['issue']
        print(pre_draw_date, ' ', str(issue) + '期')

        # 拿到正码
        pre_draw_code = body_list['preDrawCode']
        pre_draw_code_list = pre_draw_code.split(',')

        mark_six_result(pre_draw_code_list)

