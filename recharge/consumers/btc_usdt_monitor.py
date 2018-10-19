from users.models import UserRecharge, UserCoin, Coin
from base.eth import Wallet
from decimal import Decimal
import math
import requests
import json
import time
from utils.cache import set_cache

OMNI_URL = 'https://api.omniexplorer.info/v1/transaction/tx/'
BTC_DECIMAL = 100000000


def get_usdt_transaction(txid):
    """
    获取USDT交易数据
    :param txid:
    :return:
    """
    usdt_resp = requests.get(OMNI_URL + txid, headers={'content-type': 'application/json'})
    usdt_data = json.loads(usdt_resp.text)

    response = None
    if 'amount' in usdt_data:
        response = {
            'txid': txid,
            'value': usdt_data['amount'],
        }

    return response


def consumer_bitcoin_usdt_monitor(block_num):
    """
    消费block_num队列
    """
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    print('当前获取块高值 =', block_num)

    # 根据block_num 获取交易数据
    wallet = Wallet()
    json_obj = wallet.get(url='https://chain.api.btc.com/v3/block/' + str(block_num) + '/tx')
    block = json_obj['data']
    block_time = block['list'][0]['block_time']

    # 计算出总页数
    total_page = int(math.ceil(block['total_count'] / block['pagesize']))
    print('总页数 =', total_page)

    if total_page > 1:
        for page in range(2, total_page + 1):
            # 先睡个0.5秒
            time.sleep(0.5)
            json_obj = wallet.get(url='https://chain.api.btc.com/v3/block/' + str(block_num) + '/tx?page=' + str(page))
            if type(json_obj) is str:
                print('json_obj = ', str(json_obj))
                return False

            if 'list' not in json_obj['data']:
                print('json_obj is ', str(json_obj))
                return False

            block['list'] += json_obj['data']['list']

    to_address = []
    address_tx = {}
    for index, item in enumerate(block['list']):
        outputs = item['outputs']
        for output in outputs:
            addresses = output['addresses']
            txid = item['hash']
            value = output['value']
            if len(addresses) == 0 or value == 0:
                continue

            # 如果value的值等于546，则有可能是USDT的交易数据，从OMNI平台中获取交易数据
            maybe_usdt_tx = True if value == 546 else False

            to_address += addresses
            for address in addresses:
                if address not in address_tx:
                    address_tx[address] = []

                address_tx[address].append({
                    'txid': txid,
                    'maybe_usdt': maybe_usdt_tx,
                    'value': value / BTC_DECIMAL,
                })

    in_address = UserCoin.objects.filter(coin_id__in=[Coin.BTC, Coin.USDT], address__in=to_address).values('address', 'user_id', 'coin_id')
    if len(in_address) == 0:
        print('暂无充值记录')
        return True

    # 所有充值记录
    charge_all = UserRecharge.objects.filter(coin_id__in=[Coin.BTC, Coin.USDT])
    txids = []
    for charge in charge_all:
        txids.append(charge.txid)

    # 把该地址对应的交易信息拿出来
    recharge_number = 0
    for user_coin in in_address:
        address = user_coin['address']
        address_recharges = address_tx[address]

        for recharge in address_recharges:
            txid = recharge['txid']
            amount = recharge['value']
            coin_id = Coin.BTC
            coin_name = 'BTC'

            if recharge['maybe_usdt']:
                usdt_recharge = get_usdt_transaction(txid)
                txid = usdt_recharge['txid']
                amount = usdt_recharge['value']
                coin_id = Coin.USDT
                coin_name = 'USDT'

            if user_coin['coin_id'] != coin_id:
                continue

            if txid in txids:
                continue

            recharge_obj = UserRecharge()
            recharge_obj.address = address
            recharge_obj.coin_id = coin_id
            recharge_obj.txid = txid
            recharge_obj.user_id = user_coin['user_id']
            recharge_obj.amount = Decimal(str(amount))
            recharge_obj.confirmations = 0
            recharge_obj.trade_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block_time))
            recharge_obj.save()

            print('获取1条' + coin_name + '充值记录，TX = ', txid, ' Address = ', address, ' 充值金额 = ', amount)

            recharge_number += 1

    # 有充值记录则写入缓存，缓解监听交易的数据库操作压力
    if recharge_number > 0:
        set_cache('key_btc_usdt_transactions', 1)

    print('块=' + str(block_num) + ' 获取到' + str(recharge_number) + '条交易信息')
    return True
