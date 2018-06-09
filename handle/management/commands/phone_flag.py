# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
import os
from api.settings import BASE_DIR


class Command(BaseCommand):
    help = "phone flag"

    def handle(self, *args, **options):
        os.chdir(BASE_DIR + '/cache')
        url = 'http://quhao.tianqi.com/worldall/'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        for dt in list(soup.find_all('tbody')[0].find_all('tr'))[1:]:
            name_cn = str(dt.find_all('td')[0].string)
            name_en = str(dt.find_all('td')[1].string)
            quhao = str(dt.find_all('td')[2].a['title'])

            with open('phone_flag.txt', 'a+') as f:
                f.write(name_cn + ' ' + name_en + ' ' + quhao)
                f.write('\n')

