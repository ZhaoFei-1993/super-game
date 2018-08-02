from base.eth import *
import time as format_time
from users.models import UserRecharge, Coin, UserCoin


def get_coin_id(coin_type):
    """
    获取币种ID
    :param coin_type:
    :return:
    """
    coin_id = Coin.ETH
    if coin_type == 'HAND':
        coin_id = Coin.HAND
    elif coin_type == 'INT':
        coin_id = Coin.INT

    return coin_id


def etheruem_monitor(block_num):
    """
    消费block_num队列
    """
    eth_wallet = Wallet()

    print('block_num = ', block_num)
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = eth_wallet.get(url='v1/chain/blocknum/' + str(block_num))
    if json_obj['code'] != 0:
        print('根据block_num获取数据失败')
        return True

    items = json_obj['data']['data']

    charge_all = UserRecharge.objects.all()  # 所有充值记录
    txids = []
    for charge in charge_all:
        txids.append(charge['txid'])

    to_address = []
    for i, val in enumerate(items):
        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = val['type'].upper()

        to_address.append(val['to'])

    user_coin = UserCoin.objects.filter(address__in=to_address)
    if len(user_coin) == 0:
        print('该块无充值信息')
        return True

    # 地址去重
    recharge_address = []
    recharge_userid = {}
    for uc in user_coin:
        address = uc['address']
        if address in recharge_address:
            continue

        recharge_address.append(uc['address'])
        recharge_userid[uc['address']] = uc['user_id']

    # 获取去重后的地址充值信息
    recharge_info = []
    for i, val in enumerate(items):
        if val['to'] not in recharge_address or val['hash'] in txids:
            continue

        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = val['type'].upper()
        recharge_info.append(tmp_dict)

    # 插入充值记录表
    for item in recharge_info:
        time_local = format_time.localtime(item['t_time'])
        time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)

        recharge_obj = UserRecharge()
        recharge_obj.address = item['to']
        recharge_obj.coin_id = get_coin_id(item['type'])
        recharge_obj.txid = item['hash']
        recharge_obj.user_id = recharge_userid[item['to']]
        recharge_obj.amount = item['value']
        recharge_obj.confirmations = 0
        recharge_obj.trade_at = time_dt
        recharge_obj.save()

    return True
