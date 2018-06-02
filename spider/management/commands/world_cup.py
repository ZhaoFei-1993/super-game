# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from quiz.models import Quiz, Category
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
import os
from wc_auth.models import Admin


base_url = 'https://www.24zbw.com/live/zuqiu/shijiebei/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR + '/uploads/images/spider/football/team_icon'


class Command(BaseCommand):
    help = "world cup"

    def handle(self, *args, **options):
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        data = soup.select('div[class="schedule_details group_list"]')[0]
        for dt_ul in data.find_all('ul')[1:]:
            if len(dt_ul) <= 1:
                pass
            else:
                for dt_li in dt_ul.find_all('li'):
                    time = '2018-' + dt_li.select('time[class="time"]')[0].string
                    left_team = dt_li.select('div[class="score left_text"]')[0].span.a.string
                    left_team_img_url = dt_li.select('div[class="score left_text"]')[0].img['src']
                    right_team = dt_li.select('div[class="score right_text"]')[0].span.a.string
                    right_team_img_url = dt_li.select('div[class="score right_text"]')[0].img['src']

                    left_img_name = ''
                    for dt_name in left_team_img_url.split('//')[1].split('/')[1:-1]:
                        left_img_name = left_img_name + dt_name + '_'
                    left_img_name = left_img_name + left_team_img_url.split('//')[1].split('/')[-1]

                    right_img_name = ''
                    for dt_name in right_team_img_url.split('//')[1].split('/')[1:-1]:
                        right_img_name = right_img_name + dt_name + '_'
                    right_img_name = right_img_name + right_team_img_url.split('//')[1].split('/')[-1]

                    files = []
                    for root, sub_dirs, files in os.walk(img_dir):
                        files = files

                    if left_img_name not in files:
                        response_img = requests.get(left_team_img_url)
                        img = response_img.content
                        os.chdir(img_dir)
                        with open(left_img_name, 'wb') as f:
                            f.write(img)
                    else:
                        print('图片已经存在')

                    if right_img_name not in files:
                        response_img = requests.get(right_team_img_url)
                        img = response_img.content
                        os.chdir(img_dir)
                        with open(right_img_name, 'wb') as f:
                            f.write(img)
                    else:
                        print('图片已经存在')

                    if Quiz.objects.filter(host_team=left_team, guest_team=right_team).exists() is not True:
                        quiz = Quiz()
                        quiz.category = Category.objects.get(pk=873)
                        quiz.host_team = left_team
                        quiz.host_team_avatar = MEDIA_DOMAIN_HOST + '/' + left_img_name
                        quiz.guest_team = right_team
                        quiz.guest_team_avatar = MEDIA_DOMAIN_HOST + '/' + right_img_name
                        quiz.match_name = '世界杯'
                        quiz.begin_at = time
                        quiz.admin = Admin.objects.filter(id=1).first()
                        quiz.save()

                    print('成功')
                    print('----------------------------------------')
