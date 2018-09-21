from base.base_consumers import BaseConsumer


class GuessPKConsumer(BaseConsumer):
    async def receive_json(self, content, **kwargs):
        """
        接收客户端传过来的json数据
        1. 客户端连接成功后发送join指令，组名为：guess_pk_{issue_id}
        2. 客户端需做心跳包，保持websocket连接不间断
        :param content:
        :param kwargs:
        :return:
        """
        command = content.get("command", None)  # 指令
        group_name = content.get("group")  # 消息组

        if command == 'join':
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def detail_message(self):
        await self.send_json({
            "msg_type": "detail",
        })

    async def result_list_message(self):
        await self.send_json({
            "msg_type": "result_list",
        })
