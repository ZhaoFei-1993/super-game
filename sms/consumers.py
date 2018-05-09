import http.client
import json

from sms.models import Sms


def send_sms(sms_id):
    """
    发送短信队列
    """
    # 服务地址
    host = "intapi.253.com"

    # 端口号
    port = 80

    # 版本号
    version = "v1.1"

    # 查账户信息的URI
    balance_get_uri = "/balance/json"

    # 智能匹配模版短信接口的URI
    sms_send_uri = "/send/json"

    # 创蓝账号
    account = "I2621746"

    # 创蓝密码
    password = "VMetsvLuzq9496"

    sms = Sms.objects.get(pk=sms_id)

    params = {'account': account, 'password': password, 'msg': sms.message, 'mobile': sms.telephone, 'report': 'false'}
    params = json.dumps(params)

    headers = {"Content-type": "application/json"}
    conn = http.client.HTTPConnection(host, port=port, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()

    response_str = response_str.decode('utf-8')
    result = json.loads(response_str)
    if int(result['code']) == 0:
        sms.status = Sms.SUCCESS
        sms.save()
    return True


def get_user_balance(account, password, host, port, balance_get_uri):
    """
    取账户余额
    """
    params = {'account': account, 'password': password}
    params = json.dumps(params)

    headers = {"Content-type": "application/json"}
    conn = http.client.HTTPConnection(host, port=port)
    conn.request('POST', balance_get_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str
