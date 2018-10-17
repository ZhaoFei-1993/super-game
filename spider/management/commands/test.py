# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from time import sleep
import random

cookies = 'UM_distinctid=16620e83c8e59c-04953c8dc32a3-346a7809-1aeaa0-16620e83c8f268; ebxcustomer_id=0; PHPSESSID=t5e3v140r1601f2d44bkisg1q1; CNZZDATA752257=cnzz_eid%3D330427788-1538149668-%26ntime%3D1538396408; Hm_lvt_eb2d8c3f85218735466243637b14de44=1538150383,1538191668,1538396742; Hm_lpvt_eb2d8c3f85218735466243637b14de44=1538396800'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Connectin': 'close',
    # 'Cookie': cookies
}

old_proxy = ''


# 可做成代理池形式,redis等
def get_proxies(switch=False):
    test_url = 'http://httpbin.org/get'
    proxy_url = 'http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId=8b9a4db76abd488aac105720adf9facc&orderno=YZ20181064625V25hob&returnType=2&count=1'
    while True:
        # # 获取旧的代理
        # if len(old_proxy) != 0 and switch is False:
        #     proxies = {
        #         'http': 'http://' + old_proxy,
        #         'htt[s': 'https://' + old_proxy
        #     }
        # else:
        response_proxy = requests.get(proxy_url)
        proxy_json = response_proxy.json()
        print(proxy_json)
        if proxy_json['ERRORCODE'] != 0:
            proxy = '{ip}:{port}'.format(ip=proxy_json['RESULT'][0]['ip'], port=proxy_json['RESULT'][0]['port'])
            proxies = {
                'http': 'http://' + proxy,
                'https': 'https://' + proxy
            }
            # old_proxy = proxy
        else:
            proxies = None

        # 测试代理是否可用
        test_url = 'http://httpbin.org/get'
        if proxies is not None:
            try:
                response = requests.get(test_url, proxies=proxies, timeout=10)
                if response.status_code == 200:
                    print(response.text)
                    print('proxy pass')
                    return proxies
            except Exception as e:
                print('Error', e.args)

        # 不可用代理地址延迟再获取
        sleep(5)


def get_search_page(register_code, proxies):
    # 搜索页
    links = []
    url = 'https://www.eb.com.cn/trademark/searchlist?keywords=' + register_code
    response = requests.get(url=url, headers=headers, proxies=proxies, timeout=20)
    soup = BeautifulSoup(response.content, 'lxml')

    if len(soup.find_all('h1')[0].text) == '消息提示':
        return False

    print(response.text)

    for li_tag in soup.select('div[class="content-inq-con"]')[0].find('ul').find_all('li'):
        link = li_tag.find_all('div')[0].find('a')['href']
        links.append(link)
    print(links)
    return links


def get_detail_page(link, proxies):
    # 详情页
    base_url = 'https://www.eb.com.cn'

    print(base_url + link)
    try:
        response_detail = requests.get(url=base_url + link, headers=headers, proxies=proxies, timeout=20)
    except Exception as e:
        print('Error', e.args)
        return False

    soup_detail = BeautifulSoup(response_detail.content, 'lxml')
    i = 0
    for tr_tag in soup_detail.find('tbody').find_all('tr'):
        i += 1
        if i == 1:
            print('申请人: ', tr_tag.find_all('td')[1].find('span').text)
        elif i == 3:
            print('商标状态: ', tr_tag.find_all('td')[1].text)
            print('注册号: ', tr_tag.find_all('td')[3].text)
            print('类别: ', tr_tag.find_all('td')[5].text)
        elif i == 4:
            print('图片后缀: ', 'https:' + tr_tag.find_all('td')[1].find('img')['src'].replace(' ', ''))
            type_list = []
            for li_tag in tr_tag.find_all('td')[3].find_all('li'):
                type_list.append(li_tag.text)
            print('商品／服务列表: ', ', '.join(type_list))
        elif i == 5:
            print('初审公告期号: ', tr_tag.find_all('td')[1].find('span').text)
            print('初审公告日期: ', tr_tag.find_all('td')[3].text)
            print('申请日期: ', tr_tag.find_all('td')[5].text)
        elif i == 6:
            print('注册公告期号: ', tr_tag.find_all('td')[1].find('span').text)
            print('注册公告日期: ', tr_tag.find_all('td')[3].text)
            print('商标类型: ', tr_tag.find_all('td')[5].text)
        elif i == 11:
            # 商标公告
            print(tr_tag.find_all('td')[1].find('p').text.replace(' ', '').replace('\n', ''))
        else:
            print(tr_tag.select('td[class="td-title"]')[0].text, ': ',
                  tr_tag.find_all('td')[1].text.replace(' ', ''))
    print('-----------------------------------------------')
    return True


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # while True均为代理请求失败重新获取新代理地址而设置
        # register_code = '15951098'
        # i = 0
        # while True:
        #     i += 1
        #     proxies = get_proxies()
        #     if i > 1:
        #         proxies = get_proxies(switch=True)
        #     print('正在使用代理:', proxies)
        #
        #     links = get_search_page(register_code, proxies)
        #     if links is False:
        #         continue
        #
        #     for link in links:
        #         while True:
        #             flag = get_detail_page(link, proxies)
        #             if flag is True:
        #                 break
        #             else:
        #                 proxies = get_proxies(switch=True)
        #     break

        # path = '/Users/lvwenqi/Downloads'
        # url = 'http://wswj.saic.gov.cn:8080/images/TID/201102/613/DA561557CF779A261B57144B1C7BFBB1/25/ORI.JPG'
        # response = requests.get(url, headers=headers)
        # print(response.status_code)
        # import os
        # os.chdir(path)
        # with open('ORI.JPG', 'wb') as f:
        #     f.write(response.content)
        # print('go')

        from marksix.models import MarkSixBetLimit
        for id in [100, 101]:
            for i in MarkSixBetLimit.objects.filter(options_id=99):
                mark_six_betlimit = MarkSixBetLimit()
                mark_six_betlimit.max_limit = i.max_limit
                mark_six_betlimit.min_limit = i.min_limit
                mark_six_betlimit.club_id = i.club_id
                mark_six_betlimit.options_id = id
                mark_six_betlimit.save()


















