import time as format_time
from users.models import UserRecharge, Coin, UserCoin
from base.function import curl_get
from ethereum.abi import (
    decode_abi,
    normalize_name as normalize_abi_method_name,
    method_id as get_abi_method_id)
from ethereum.utils import encode_int, zpad, decode_hex
from base.tokens import TOKENS
from django.conf import settings


def deal_db_data(trans_dict, coin_all, charge_all):
    # 币种是否配置
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


def get_api_url(querystring):
    return settings.ETHERSCAN_API_URL + querystring + '&apikey=' + settings.ETHERSCAN_API_KEY


def get_coin_info(to_address, inputs, value):
    """
    币种类型，根据transaction的to值来判断，对于代币交易，to的值即为合约地址
    :param to_address:  转发接收地址
    :param inputs:      代币转账数据
    :param value:       转账金额
    :return: coin_type, to_address, transfer_value
    """
    coin_type = 'ETH'
    decimal = pow(10, 18)
    contract_abi = None
    for token in TOKENS:
        if to_address == TOKENS[token]['address']:
            coin_type = token
            decimal = TOKENS[token]['decimal']
            contract_abi = TOKENS[token]['abi']
            break

    if contract_abi is None:
        tx_value = int(value, 0) / decimal
        return coin_type, to_address, tx_value

    # 代币转账解析inputs数据获取转账接收地址、转账金额
    inputs_bin = decode_hex(inputs)
    method_signature = inputs_bin[:4]
    for description in contract_abi:
        if description.get('type') != 'function':
            continue

        method_name = normalize_abi_method_name(description['name'])
        arg_types = [item['type'] for item in description['inputs']]
        method_id = get_abi_method_id(method_name, arg_types)
        if method_name != 'transfer' or zpad(encode_int(method_id), 4) != method_signature:
            continue

        try:
            args = decode_abi(arg_types, inputs_bin[4:])
        except AssertionError:
            continue

    tx_value = args[1] / decimal
    return coin_type, args[0], tx_value


def etheruem_monitor(block_num):
    """
    以太坊充值监控
    """
    if block_num is 'None':
        print('队列暂时无数据')
        return True

    # 根据block_num 获取交易数据
    json_obj = curl_get(url=get_api_url('eth_getBlockByNumber&tag=' + hex(block_num) + '&boolean=true'))
    if 'error' in json_obj:
        return False

    items = json_obj['result']['transactions']

    coin_all = Coin.objects.all()  # 所有币种
    charge_all = UserRecharge.objects.all()  # 所有充值记录
    tmp_num = 0
    for i, val in enumerate(items):
        tmp_dict = val
        tmp_dict['t_time'] = int(json_obj['result']['timestamp'], 0)

        # 判断币种类型，根据transaction的to值来判断，对于代币交易，to的值即为合约地址
        coin_type, to_address, to_value = get_coin_info(val['to'], val['input'], val['value'])
        tmp_dict['type'] = coin_type
        tmp_dict['to'] = to_address
        tmp_dict['value'] = to_value

        # 根据交易信息处理db数据
        ret = deal_db_data(tmp_dict, coin_all, charge_all)
        if ret is True:
            tmp_num += 1
