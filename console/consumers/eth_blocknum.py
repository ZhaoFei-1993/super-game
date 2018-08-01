from base.eth import *
from time import time
import time as format_time
from users.models import UserRecharge, Coin, UserCoin
from base.function import curl_get

base_url = "http://47.52.18.81"


def consumer_ethblock(block_num):
    """
    消费block_num队列
    """
    eth_wallet = Wallet()
    start_time = time()

    print('block_num = ', block_num)
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = eth_wallet.get(url='v1/chain/blocknum/' + str(block_num))
    # with open('/tmp/console_consumers.log', 'a+') as f:
    #     f.write('items = ' + str(json_obj))
    #     f.write("\n")
    # print(json_obj)
    if json_obj['code'] != 0:
        print('根据block_num获取数据失败')
        return True

    items = json_obj['data']['data']
    # if str(block_num) == '5924839':
    #     with open('/tmp/console_consumers.log', 'a+') as f:
    #         f.write('items = ' + str(items))
    #         f.write("\n")

    coin_all = Coin.objects.all()  # 所有币种
    charge_all = UserRecharge.objects.all()  # 所有充值记录
    tmp_num = 0
    for i, val in enumerate(items):
        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = val['type'].upper()

        # if str(block_num) == '5924839':
        #     with open('/tmp/console_consumers.log', 'a+') as f:
        #         f.write('tmp_dict = ' + str(tmp_dict))
        #         f.write("\n")

        # 根据交易信息处理db数据
        ret = deal_db_data(tmp_dict, coin_all, charge_all)
        if ret is True:
            tmp_num += 1

    print('blocknum:' + str(block_num) + '获取到' + str(tmp_num) + '条交易信息')

    stop_time = time()
    cost_time = str(round(stop_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)
    return True


def deal_db_data(trans_dict, coin_all, charge_all):
    # dict['type'] = 'INT'
    # 币种是否存在
    coin_exists = False
    for coin in coin_all:
        if coin.name == trans_dict['type']:
            coin_exists = True
            coin_id = coin.id
            break

    if coin_exists is False:
        print('type_not allow,type:', trans_dict['type'])
        return False

    txid = trans_dict['hash']
    addr = trans_dict['to']

    # addr = '0xbc188Cc44428b38e115a2C693C9D0a4fD0BDCc71'
    value = trans_dict['value']
    t_time = trans_dict['t_time']
    usercoin_info = UserCoin.objects.filter(address=addr, coin_id=coin_id, user__is_robot=False, user__is_block=False)
    if not usercoin_info:
        return False

    user_id = usercoin_info[0].user_id

    # 用户充值记录
    charge_exists = False
    for charge_data in charge_all:
        if charge_data.address == addr and charge_data.txid == txid:
            charge_exists = True

    time_local = format_time.localtime(t_time)
    time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)

    if charge_exists is False:
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
        return True

    return False


def consumer_bchblock(block_num):
    """
    消费block_num队列
    """
    start_time = time()

    print('block_num = ', block_num)
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = curl_get(url=base_url + '/?r=bch/getblock&block' + str(block_num))

    items = json_obj['data']['data']

    coin_all = Coin.objects.all()  # 所有币种
    charge_all = UserRecharge.objects.all()  # 所有充值记录
    tmp_num = 0
    for i, val in enumerate(items):
        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = json_obj['data']['type'].upper()

        # 根据交易信息处理db数据
        ret = deal_db_data(tmp_dict, coin_all, charge_all)
        if ret is True:
            tmp_num += 1

    print('blocknum:' + str(block_num) + '获取到' + str(tmp_num) + '条交易信息')

    stop_time = time()
    cost_time = str(round(stop_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)
    return True


def consumer_ltcblock(block_num):
    """
    消费block_num队列
    """
    start_time = time()

    print('block_num = ', block_num)
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = curl_get(url=base_url + '/?r=ltc/getblock&block' + str(block_num))

    items = json_obj['data']['data']

    coin_all = Coin.objects.all()  # 所有币种
    charge_all = UserRecharge.objects.all()  # 所有充值记录
    tmp_num = 0
    for i, val in enumerate(items):
        tmp_dict = val
        tmp_dict['t_time'] = json_obj['data']['t_time']
        tmp_dict['type'] = json_obj['data']['type'].upper()

        # 根据交易信息处理db数据
        ret = deal_db_data(tmp_dict, coin_all, charge_all)
        if ret is True:
            tmp_num += 1

    print('blocknum:' + str(block_num) + '获取到' + str(tmp_num) + '条交易信息')

    stop_time = time()
    cost_time = str(round(stop_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)
    return True
