# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup

url_HSI = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=aff194940ee6db5fcb462df18a36f9fd'
url_DJA = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d'
url_SHANG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E4%B8%8A%E8%AF%81%E6%8C%87%E6%95%B0&hilight=disp_data.*.title'
url_SHENG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E6%B7%B1%E8%AF%81%E6%88%90%E6%8C%87&hilight=disp_data.*.title'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        response = requests.get(url_HSI)
        print(response.json()['data'][0]['disp_data'][0]['status'])
        print(response.json()['data'][0]['disp_data'][0]['tabs'])

