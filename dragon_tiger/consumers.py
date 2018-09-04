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


def dragon_tiger_result(table_id, number_tab_id, opening):
    """
    推送结果
    :param table_id      桌id
    :param number_tab_id     局id
    :param opening     局状态
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "result.message",
            "table_id": table_id,
            "number_tab_id": number_tab_id,
            "opening": opening
        },
    )


def dragon_tiger_showroad(table_id, show_x, show_y, result, pair):
    """
    推送结果图结果
    :param table_id      桌id
    :param show_x     x轴
    :param show_y     y轴
    :param result     结果
    :param pair     结果(对)
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "showroad.message",
            "show_x": show_x,
            "show_y": show_y,
            "result": result,
            "pair": pair
        },
    )


def dragon_tiger_bigroad(table_id, show_x, show_y, result, tie_num):
    """
    推送大路图结果
    :param table_id      桌id
    :param show_x     x轴
    :param show_y     y轴
    :param result     结果
    :param tie_num     结果(对)
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "bigroad.message",
            "show_x": show_x,
            "show_y": show_y,
            "result": result,
            "tie_num": tie_num
        },
    )


def dragon_tiger_bigeyeroad(table_id, show_x, show_y, result):
    """
    推送大眼路图结果
    :param table_id      桌id
    :param show_x     x轴
    :param show_y     y轴
    :param result     结果
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "bigeyeroad.message",
            "show_x": show_x,
            "show_y": show_y,
            "result": result
        },
    )


def dragon_tiger_pathway(table_id, show_x, show_y, result):
    """
    推送小路图结果
    :param table_id      桌id
    :param show_x     x轴
    :param show_y     y轴
    :param result     结果
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "pathway.message",
            "show_x": show_x,
            "show_y": show_y,
            "result": result
        },
    )


def dragon_tiger_roach(table_id, show_x, show_y, result):
    """
    推送珠盘路结果
    :param table_id      桌id
    :param show_x     x轴
    :param show_y     y轴
    :param result     结果
    :return:
    """
    group = 'dragon_tiger_' + str(table_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "roach.message",
            "show_x": show_x,
            "show_y": show_y,
            "result": result
        },
    )


def dragon_tiger_lottery(user_id, coins, opening, balance):
    """
    推送用户金额结果
    :param user_id      用户id
    :param coins     x轴
    :param opening     y轴
    :param balance     用户现有金额
    :return:
    """
    group = 'lottery_' + str(user_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "lottery.message",
            "coins": coins,
            "opening": opening,
            "balance": balance
        },
    )


def dragon_tiger_avatar(number_tab_id, now_avatar_list):
    """
    推送用户金额结果
    :param number_tab_id      用户id
    :param now_avatar_list     用户现有金额
    :return:
    """
    group = 'avatar_' + str(number_tab_id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "avatar.message",
            "number_tab_id": number_tab_id,
            "now_avatar_list": now_avatar_list
        },
    )
