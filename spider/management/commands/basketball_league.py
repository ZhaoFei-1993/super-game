# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import re
import requests
import json
from bs4 import BeautifulSoup
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Category
from wc_auth.models import Admin


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR+'/uploads/images/spider/basketball/league_icon'
cache_dir = BASE_DIR + '/cache'


def get_league_url():
    league_list = []
    url = 'http://info.sporttery.cn/basketball/history/data_center.php'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    match_box_list = soup.select('div[class="match-box"]')
    for match_box in match_box_list[:-1]:
        li_tags = match_box.ul.find_all('li')
        for li_tag in li_tags:
            league_list.append(li_tag.a['href'])
    for li_tag in match_box_list[-1].find_all('li'):
        league_list.append(li_tag.a['href'])
    return league_list


def get_league_info(leagua_list=[]):
    os.chdir(cache_dir)
    files = []
    for root, sub_dirs, files in os.walk(cache_dir):
        files = files
    if 'league_cache.txt' not in files:
        with open('basketball_league_cache.txt', 'a+') as f:
            pass

    base_url = 'http://i.sporttery.cn/api/bk_match_info/get_comp_seasons/?f_callback=cInfo&c_id='
    if len(leagua_list) > 0:
        for league in leagua_list:
            id = league[23:]

            with open('basketball_league_cache.txt', 'r+') as f:
                data = f.read()
            data_list = data.split(',')
            if base_url + id not in data_list:
                with open('basketball_league_cache.txt', 'a+') as f:
                    f.write(base_url + id + ',')

                response = requests.get(base_url + id)
                dt = response.text.encode("utf-8").decode('unicode_escape')
                json_dt = json.loads(dt[6:-2])

                # name = json_dt['result']['comp_name']
                name = json_dt['result']['comp_abbr']
                icon = json_dt['result']['comp_pic']

                icon_name = re.findall('http://static.sporttery.cn/sinaimg/basketball/competitionpic/(.*)', icon)[0]

                files = []
                source_dir = img_dir
                for root, sub_dirs, files in os.walk(source_dir):
                    files = files
                if icon_name not in files:
                    response_img = requests.get(icon, headers=headers)
                    img = response_img.content
                    os.chdir(img_dir)
                    with open(icon_name, 'wb') as f:
                        f.write(img)
                else:
                    print('图片已经存在')

                if Category.objects.filter(name=name).first() is not None:
                    print('联赛已存在')
                else:
                    category = Category()
                    category.name = name
                    category.icon = MEDIA_DOMAIN_HOST + '/images/spider/basketball/league_icon/' + icon_name
                    category.admin = Admin.objects.filter(id=1).first()
                    category.parent = Category.objects.filter(id=1).first()
                    category.save()

                print(name)
                print(icon)
                print('----------------------------------------------------')
            else:
                print('已经存在，跳过')
    else:
        print('无内容')


class Command(BaseCommand):
    help = "爬取篮球联赛"

    def handle(self, *args, **options):
        print(os.getcwd())
        league_list = get_league_url()
        print(league_list)
        get_league_info(league_list)
