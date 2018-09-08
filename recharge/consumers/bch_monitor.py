import time
from users.models import UserRecharge, UserCoin, Coin
from base.eth import Wallet
from decimal import Decimal
from local_settings import BCH_WALLET_API_URL


def bitcoin_cash_monitor(block_num):
    """
    消费block_num队列
    """
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    wallet = Wallet()
    json_obj = wallet.get(url=BCH_WALLET_API_URL + 'v1/bch/block/transactions/' + str(block_num))
    block = json_obj['data']

    to_address = []
    address_tx = {}
    for index, item in enumerate(block['transactions']):
        outputs = item['out']
        for output in outputs:
            addresses = output['addresses']
            to_address += addresses
            for address in addresses:
                if address not in address_tx:
                    address_tx[address] = []

                address_tx[address].append({
                    'txid': item['txid'],
                    'value': output['value'],
                })

    in_address = UserCoin.objects.filter(address__in=to_address).values('address', 'user_id')
    if len(in_address) == 0:
        return True

    # 所有充值记录
    charge_all = UserRecharge.objects.all()
    txids = []
    for charge in charge_all:
        txids.append(charge.txid)

    # 把该地址对应的交易信息拿出来
    recharge_number = 0
    for user_coin in in_address:
        address_recharges = address_tx[user_coin['address']]
        for recharge in address_recharges:
            txid = recharge['txid']
            if txid in txids:
                continue

            recharge_obj = UserRecharge()
            recharge_obj.address = user_coin['address']
            recharge_obj.coin_id = Coin.BCH
            recharge_obj.txid = txid
            recharge_obj.user_id = user_coin['user_id']
            recharge_obj.amount = Decimal(recharge['value'])
            recharge_obj.confirmations = 0
            recharge_obj.trade_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.time))
            recharge_obj.save()

            print('获取1条BCH充值记录，TX = ', txid, ' Address = ', user_coin['address'], ' 充值金额 = ', recharge['value'])

            recharge_number += 1

    print('块=' + str(block_num) + ' 获取到' + str(recharge_number) + '条交易信息')
    return True
