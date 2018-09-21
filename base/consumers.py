from django.core.management import call_command
from base.base_consumers import BaseConsumer


class QuizConsumer(BaseConsumer):
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
        elif command == 'football_synctime':
            await self.channel_layer.group_send(group_name, {
                "type": "football_time.message",
                "quiz_id": content.get("quiz_id"),
                "content": content
            })
        elif command == 'basketball_synctime':
            await self.channel_layer.group_send(group_name, {
                "type": "basketball_time.message",
                "quiz_id": content.get("quiz_id"),
            })

        # elif command == 'send':
        #     await self.channel_layer.group_send(group_name, {
        #         "type": "quiz.message",
        #         "message": content.get("message"),
        #     })

    async def command_message(self, event):
        """
        推送比分数据至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "score",
                "quiz_id": event["quiz_id"],
                "host": event["host"],
                "guest": event['guest'],
            }
        )

    async def footballsynctime_message(self, event):
        """
        推送比赛时间数据至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "football_time",
                "quiz_id": event["quiz_id"],
                "status": event["status"],
                "quiz_time": event['quiz_time'],
            }
        )

    async def basketballsynctime_message(self, event):
        """
        推送比赛时间数据至客户端
        :param event:
        :return:
        """
        await self.send_json(
            {
                "msg_type": "basketball_time",
                "quiz_id": event["quiz_id"],
                "status": event["status"],
            }
        )

    async def football_time_message(self, event):
        with open('/tmp/debug_mseeage', 'a+') as f:
            f.write(str(event))
            f.write("\n")
        quiz_id = event['quiz_id']
        if int(quiz_id) == 1312:
            pass
        else:
            call_command('football_synctime', quiz_id)

    async def basketball_time_message(self, event):
        with open('/tmp/debug_mseeage', 'a+') as f:
            f.write(str(event))
            f.write("\n")
        quiz_id = event['quiz_id']
        if int(quiz_id) == 1312:
            pass
        else:
            call_command('basketball_synctime', quiz_id)
