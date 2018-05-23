# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from console.models import Address
from users.models import Coin


class Command(BaseCommand):
    help = "导入BTC地址"

    btc_address_file = '/tmp/btc_address'

    def handle(self, *args, **options):
        with open(self.btc_address_file) as addresses:
            import_count = 0
            for line in addresses:
                index, address, private_key = line.split(',')
                address = address.replace('"', '')
                private_key = private_key.replace('"', '')

                # 查询地址是否存在
                is_address_exists = Address.objects.filter(address=address, passphrase=private_key).count()
                if is_address_exists > 0:
                    self.stdout.write(self.style.SUCCESS('地址 ' + address + ' 已经存在'))
                    continue

                # 插入地址库
                mdl_address = Address()
                mdl_address.coin_id = Coin.BTC
                mdl_address.address = address
                mdl_address.passphrase = private_key
                mdl_address.save()

                import_count += 1

            self.stdout.write(self.style.SUCCESS('成功导入 ' + str(import_count) + ' 条BTC地址'))
