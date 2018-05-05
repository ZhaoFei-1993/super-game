from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib import parse
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256
import base64

from django.conf import settings
import dateutil.parser as dateparser
import time

from django.core.cache import caches


class QuizConsumer(AsyncJsonWebsocketConsumer):
    """
    竞猜详情消费者处理类
    """
    async def connect(self):
        """
        连接websocket
        :return:
        """
        query_string = dict(parse.parse_qs(self.scope['query_string']))

        # 是否传递当前时间
        if b'time' not in query_string:
            print('no time')
            return False

        ws_time = query_string[b'time'][0].decode('utf-8')
        if ws_time == '':
            print('time is empty')
            self.disconnect(403)

        # 是否传递随机数
        if b'nonce' not in query_string:
            print('no nonce')
            return False

        ws_nonce = query_string[b'nonce'][0].decode('utf-8')
        if ws_nonce == '':
            print('nonce is empty')
            return False

        # 时间有效性，随机数判断
        api_date = dateparser.parse(ws_time)
        api_date_timestamp = time.mktime(api_date.timetuple()) + 8 * 3600
        if api_date_timestamp + 60 < time.time():
            print('websocket token expire')
            # return False

        cache = caches['redis']
        cache_key = 'ws_nonce_' + ws_nonce
        stored_nonce = cache.get(cache_key)
        if stored_nonce is None:
            cache.set(cache_key, ws_nonce, 60)
        else:
            pass
            # print('prevent reply request')
            # return False

        # 是否传递token值
        if b'token' not in query_string:
            print('no token')
            return False

        ws_token = query_string[b'token'][0].decode('utf-8')
        if ws_token == '':
            print('token is empty')
            return False

        # 判断token是否有效
        hmac = HMAC.new(settings.WEBSOCKE_SECRET.encode('ascii'), digestmod=SHA256)
        enc_string = ws_time + ws_nonce
        print('enc_string = ', enc_string)
        print('settings.WEBSOCKE_SECRET = ', settings.WEBSOCKE_SECRET)
        hmac.update(enc_string.encode('ascii'))
        signed = hmac.digest()
        calc_token = base64.b64encode(signed).decode("ascii")

        if calc_token != ws_token:
            print('calc_token = ', calc_token)
            print('ws_token = ', ws_token)
            print('token is invalid')
            return False

        await self.accept()

    async def disconnect(self, code):
        """
        关闭websocket
        :param code:
        :return:
        """
        print('call disconnect')

    async def receive_json(self, content, **kwargs):
        """
        接收客户端传过来的json数据
        1. 客户端连接成功后发送join指令，组名为：quiz_{quiz_id}
        2. 客户端需做心跳包，保持websocket连接不间断
        3. 服务端推送指定组的实时比分指令(score)，客户端接收指令并处理
        :param content:
        :param kwargs:
        :return:
        """
        command = content.get("command", None)  # 指令
        group_name = content.get("group")       # 消息组

        if command == 'join':
            await self.channel_layer.group_add(group_name, self.channel_name)
        # elif command == 'send':
        #     await self.channel_layer.group_send(group_name, {
        #         "type": "quiz.message",
        #         "message": content.get("message"),
        #     })

    async def command_message(self, event):
        """
        推送数据至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "score",
                "host": event["host"],
                "guest": event['guest'],
            }
        )
