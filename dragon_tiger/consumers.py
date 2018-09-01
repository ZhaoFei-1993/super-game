# -*- coding: UTF-8 -*-
from channels.consumer import get_channel_layer
from asgiref.sync import async_to_sync


def dragon_tiger_table_info(table_id, in_checkout):
    """
    桌子状态
     :param table_id 桌ID
    :param in_checkout    桌状态
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "tableinfo.message",
            "table_id": table_id,
            "in_checkout": in_checkout
        },
    )


def dragon_tiger_boots_info(table_id, boots_id, boot_num):
    """
    推送局信息
    :param table_id:
    :param boots_id:
    :param boot_num:
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "bootsinfo.message",
            "table_id": table_id,
            "boots_id": boots_id,
            "boot_num": boot_num
        },
    )


def dragon_tiger_number_info(table_id, number_tab_id, bet_statu):
    """
    number 推送
    :param table_id 桌ID
    :param number_tab_id    局id
    :param bet_statu    局状态
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "numberinfo.message",
            "table_id": table_id,
            "number_tab_id": number_tab_id,
            "betstatus": bet_statu
        },
    )


# def dragon_tiger_ready_bet(table_id, in_checkout, number_tab_id, bet_statu):
#     """
#     发送比分
#     :param table_id      桌id
#     :param in_checkout      桌状态
#     :param number_tab_id     局id
#     :param bet_statu     局状态
#     :return:
#     """
#     group = 'dragon_tiger_' + str(table_id)
#
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         group,
#         {
#             "type": "readybet.message",
#             "table_id": table_id,
#             "in_checkout": in_checkout,
#             "number_tab_id": number_tab_id,
#             "bet_statu": bet_statu
#         },
#     )

