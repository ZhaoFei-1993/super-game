# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import json
import requests
from users.models import UserCoin, UserRecharge, Coin, User, CoinDetail
from utils.cache import set_cache, get_cache, delete_cache
from decimal import Decimal
import time
from utils.functions import is_number
from django.conf import settings


class Command(BaseCommand):
    """
    EOS充值账号转账监控，5秒查询一次--eospark.com平台
    为减少UserRecharge表的数据库查询次数，缓存EOS所有TXID（文件缓存），有新交易产生后重新生成缓存
    """
    help = "EOS充值监控--eospark.com平台"
    cache_txid_key = 'key_eos_txid_eospark'
    cache_invalid_memo_key = 'key_eos_invalid_memo_eospark'
    eos_monitor_url = 'https://api.eospark.com/api?module=account&action=get_account_related_trx_info&apikey=4a73296ca87b57296cd93cc09af5d9f9&account=' + settings.EOS_RECHARGE_ADDRESS + '&page=1&size=100&symbol=EOS&code=eosio.token'

    def handle(self, *args, **options):
        # post_data = '{"interface_name":"get_account_related_trx_info","tab_name":"token","account_name":"supergameeos","page_num":1,"page_size":50,"hide_small_quantity":1}'
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
        response = requests.get(url=self.eos_monitor_url, headers={'User-Agent': user_agent})
        transfers = json.loads(response.text)

        eos_cache_txid = get_cache(self.cache_txid_key, 'default')
        if eos_cache_txid is not None:
            tx_ids = eos_cache_txid
        else:
            # 获取所有已充值的EOS交易记录
            user_recharges = UserRecharge.objects.filter(coin_id=Coin.EOS)
            tx_ids = []
            for user_recharge in user_recharges:
                tx_ids.append(user_recharge.txid)
            set_cache(self.cache_txid_key, tx_ids, -1, 'default')

        # 无效的充值MEMO
        invalid_memos = get_cache(self.cache_invalid_memo_key, 'default')
        if invalid_memos is None:
            invalid_memos = []

        transactions = []
        memos = []
        for transfer in transfers['data']['trace_list']:
            memo = transfer['memo']
            tx_hash = transfer['trx_id']
            ts = time.strptime(transfer['timestamp'].replace('T', ' '), '%Y-%m-%d %H:%M:%S.%f')

            if transfer['receiver'] != settings.EOS_RECHARGE_ADDRESS or transfer['code'] != 'eosio.token' or transfer['status'] != 'executed' or transfer['symbol'] != 'EOS':
                continue

            # 判断MEMO值是否为数字，非数字则为无效充值记录
            if is_number(memo) is False:
                continue

            # 判断该充值交易号是否已经入账
            if tx_hash in tx_ids:
                continue

            memo = int(memo)
            if memo in invalid_memos:
                continue

            memos.append(memo)

            transactions.append({
                'txid': tx_hash,
                'amount': transfer['quantity'],
                'memo': memo,
                'time': int(time.mktime(ts)) + 8 * 3600,
            })

        if len(transactions) == 0:
            raise CommandError('暂无充值记录')

        print('获取到', len(transactions), '条交易记录')
        memos = list(set(memos))

        users = User.objects.filter(eos_code__in=memos)
        if len(users) == 0:
            invalid_memos += memos
            set_cache(self.cache_invalid_memo_key, invalid_memos, -1, 'default')
            raise CommandError('暂无有效充值记录')

        is_modified_invalid_memos = False
        count_valid_recharge = 0
        for user in users:
            for transaction in transactions:
                memo = transaction['memo']

                if memo != user.eos_code:
                    is_modified_invalid_memos = True
                    # 无效充值MEMO
                    if memo not in invalid_memos:
                        invalid_memos.append(memo)
                    continue

                txid = transaction['txid']
                amount = transaction['amount']
                user_id = user.id
                trade_at = time.localtime(transaction['time'])

                ur = UserRecharge()
                ur.address = memo
                ur.coin_id = Coin.EOS
                ur.txid = txid
                ur.user_id = user_id
                ur.amount = Decimal(amount)
                ur.confirmations = 0
                ur.trade_at = time.strftime("%Y-%m-%d %H:%M:%S", trade_at)
                ur.save()

                # user coin增加对应值
                user_coin = UserCoin.objects.get(coin_id=Coin.EOS, user_id=user_id)
                user_coin.balance += Decimal(amount)
                user_coin.save()

                coin_detail = CoinDetail()
                coin_detail.user_id = user_id
                coin_detail.coin_name = 'EOS'
                coin_detail.amount = amount
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.RECHARGE
                coin_detail.save()

                print('获取一条EOS充值', amount, 'MEMO', memo, 'TXID为', txid)
                count_valid_recharge += 1

        print('获得', count_valid_recharge, ' 条有效充值记录')
        delete_cache(self.cache_txid_key, 'default')
        if is_modified_invalid_memos:
            set_cache(self.cache_invalid_memo_key, invalid_memos, -1, 'default')
        self.stdout.write(self.style.SUCCESS('执行完成'))
