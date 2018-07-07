from base.eth import *
from time import time
import time as format_time
from decimal import Decimal
from users.models import UserRecharge, Coin, UserCoin, CoinDetail, User


def consumer_ethblock(block_num):
    """
    消费block_num队列
    """
    help = "消费ETH_blocknum获取取交易数据"
    eth_wallet = Wallet()
    start_time = time()

    print(block_num)
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = eth_wallet.get(url='/api/v1/chain/blocknum/' + str(block_num))
    print(json_obj)
    if json_obj['code'] != 0:
        print('根据block_num获取数据失败')
        return True

    list = json_obj['data']['data']
    print(list)

    tmp_num = 0
    for i, val in enumerate(list):
        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = val['type'].upper()

        # 根据交易信息处理db数据
        ret = dealDbData(tmp_dict)
        if ret is True:
            tmp_num += 1

    print('blocknum:' + str(block_num) +'获取到' + str(tmp_num) + '条交易信息')

    stop_time = time()
    cost_time = str(round(stop_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)
    return True


def dealDbData(dict):
    # dict['type'] = 'INT'
    info = Coin.objects.filter(name=dict['type'])
    if not info:
        print('type_not allow,type:', dict['type'])
        return False

    coin_id = info[0].id
    txid = dict['hash']
    addr = dict['to']

    #addr = '0xbc188Cc44428b38e115a2C693C9D0a4fD0BDCc71'
    value = dict['value']
    t_time = dict['t_time']
    usercoin_info = UserCoin.objects.filter(address=addr, coin_id=coin_id)
    if not usercoin_info:
        return False

    user_id = usercoin_info[0].user_id

    #用户充值记录
    charge_info = UserRecharge.objects.filter(address=addr, txid=txid)
    if charge_info:
        print('addr___', charge_info[0].address)

    time_local = format_time.localtime(t_time)
    time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)

    if not charge_info:
        # 充值记录
        recharge_obj = UserRecharge()
        recharge_obj.address = addr
        recharge_obj.coin_id = coin_id
        recharge_obj.txid = txid
        recharge_obj.user_id = user_id
        recharge_obj.amount = value
        recharge_obj.confirmations = 0
        recharge_obj.trade_at = time_dt
        recharge_obj.save()

        # 刷新用户余额表
        usercoin_info[0].balance += Decimal(value)
        usercoin_info[0].save()

        # 用户余额变更记录
        coin_detail = CoinDetail()
        coin_detail.user_id = user_id
        coin_detail.coin_name = dict['type']
        coin_detail.amount = value
        coin_detail.rest = usercoin_info[0].balance
        coin_detail.sources = CoinDetail.RECHARGE
        coin_detail.save()
        return True

    return False
