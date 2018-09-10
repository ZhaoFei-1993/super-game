import time
from users.models import UserRecharge, User, Coin
from base.eth import Wallet
from decimal import Decimal
from local_settings import EOS_WALLET_API_URL
from datetime import datetime
from utils.functions import convert_localtime


def electro_optical_system_monitor(block_num):
    """
    消费block_num队列
    """
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据 block_num 获取交易数据
    wallet = Wallet()
    json_obj = wallet.get(url=EOS_WALLET_API_URL + 'v1/eos/block/transactions/' + str(block_num))
    block = json_obj['data']

    # 格式化时间
    block_time = block['time']
    t_year = int(block_time[:4])
    t_month = int(block_time[5:7])
    t_day = int(block_time[8:10])
    t_hour = int(block_time[11:13])
    t_minute = int(block_time[14:16])
    t_second = int(block_time[17:19])
    t_msecond = int(block_time[20:23])
    block_time = datetime(t_year, t_month, t_day, t_hour, t_minute, t_second, t_msecond)

    to_memos = []
    memo_tx = {}
    for index, item in enumerate(block['transactions']):
        outputs = item['out']
        for output in outputs:
            memos = output['memo']
            to_memos += memos
            for memo in memos:
                if memo not in memo_tx:
                    memo_tx[memo] = []

                memo_tx[memo].append({
                    'txid': item['txid'],
                    'value': output['value'],
                    'memo': output['memo'],
                })

    in_memo = User.objects.filter(eos_code__in=to_memos).values('id', 'eos_code')
    if len(in_memo) == 0:
        return True

    # 所有充值记录
    charge_all = UserRecharge.objects.all()
    txids = []
    for charge in charge_all:
        txids.append(charge.txid)

    # 把该地址对应的交易信息拿出来
    recharge_number = 0
    for user in in_memo:
        memo_recharges = memo_tx[user['eos_code']]
        for recharge in memo_recharges:
            txid = recharge['txid']
            if txid in txids:
                continue

            recharge_obj = UserRecharge()
            recharge_obj.address = user['eos_code']
            recharge_obj.coin_id = Coin.EOS
            recharge_obj.txid = txid
            recharge_obj.user_id = user['id']
            recharge_obj.amount = Decimal(recharge['value'])
            recharge_obj.confirmations = 0
            recharge_obj.trade_at = convert_localtime(block_time)
            # recharge_obj.save()

            # user coin增加对应值

            print('获取1条EOS充值记录，TX = ', txid, ' 充值码 = ', str(user['eos_code']), ' 充值金额 = ', recharge['value'])

            recharge_number += 1

    print('块=' + str(block_num) + ' 获取到' + str(recharge_number) + '条交易信息')
    return True
