from base.base_consumers import BaseConsumer


class DragonTigerConsumer(BaseConsumer):
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
        group_name = content.get("group")  # 消息组

        if command == 'join':
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def command_message(self, event):
        """
        推送比分数据至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "score",
                "quiz_id": event["table_id"],
                "host": event["boots"],
                "guest": event['guest'],
            }
        )
