from base.base_consumers import BaseConsumer


class GuessConsumer(BaseConsumer):
    async def receive_json(self, content, **kwargs):
        """
        接收客户端传过来的json数据
        1. 客户端连接成功后发送join指令，组名为：period_{id} 或 guess_pk_{issue_id}
        2. 客户端需做心跳包，保持websocket连接不间断
        :param content:
        :param kwargs:
        :return:
        """
        command = content.get("command", None)  # 指令
        group_name = content.get("group")  # 消息组

        if command == 'join':
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def detail_message(self, event):
        await self.send_json({
            "msg_type": "detail",
        })

    async def result_list_message(self, event):
        await self.send_json({
            "msg_type": "result_list",
        })

    async def stock_message(self, event):
        """
        推送封盘状态至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "stock_seal",
                "period_id": event["period_id"],
                "period_status": event["period_status"],
            }
        )

    async def guess_graph_message(self, event):
        await self.send_json({
            "msg_type": "index_dic" + '_' + event['group'].split('_')[-1],
            "index_dic": event['index_dic'],
        })

    async def index_message(self, event):
        await self.send_json({
            "msg_type": "index",

            "left_index_value": event['left_index_value'],
            "left_index_color": event['left_index_color'],

            "right_index_value": event['right_index_value'],
            "right_index_color": event['right_index_color'],
        })
