# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import re
import requests
from bs4 import BeautifulSoup
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Category
from wc_auth.models import Admin


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR+'/uploads/images/spider/football/league_icon'


def get_league_url():
    league_list = []
    url = 'http://info.sporttery.cn/football/history/data_center.php'
    response = requests.get(url, headers=headers)
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
    base_url = 'http://info.sporttery.cn/football/history/'
    if len(leagua_list) > 0:
        for league in leagua_list:
            response = requests.get(base_url + league, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')

            name = soup.select('h2[class="title"]')[0].string
            icon = soup.select('div[class="badge"]')[0].img['src']

            icon_name = re.findall('http://static.sporttery.cn/sinaimg/football/competitionpic/(.*)', icon)[0]

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
                category.icon = MEDIA_DOMAIN_HOST + '/images/spider/football/league_icon/' + icon_name
                category.admin = Admin.objects.filter(id=1).first()
                category.parent = Category.objects.filter(id=2).first()
                category.save()

            print(name)
            print(icon)
            print('----------------------------------------------------')
    else:
        print('无内容')


class Command(BaseCommand):
    help = "爬取足球足球联赛"

    def handle(self, *args, **options):
        league_list = get_league_url()
        get_league_info(league_list)
