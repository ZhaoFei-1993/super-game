from base.backend import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView
from django.http import JsonResponse
from .authentication import TokenAuthentication
from utils.functions import value_judge
from rest_framework_jwt.settings import api_settings
import hashlib
from base import code as error_code
from base.exceptions import ParamErrorException
from wc_auth.models import Admin
import time
from .functions import get_now, get_range_time, verify_date,CountPage
from users.models import UserRecharge, UserPresentation, UserCoin, CoinDetail, UserMessage, User
from chat.models import Club
from django.db.models import Sum, Q
from quiz.models import Record, OptionOdds


class UserManager(object):
    """用户处理类"""

    def get_access_token(self, user):
        """
        获取access_token
        :param user:
        :return:
        """
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return token

    @staticmethod
    def verify_pwd(password):
        password = hashlib.sha1(password.encode()).hexdigest()
        return password

    def login(self, username, password):
        password = self.verify_pwd(password)
        try:
            usr = Admin.objects.get(username=username, password=password)
            usr.last_login = get_now()
            usr.save()
        except:
            raise ParamErrorException(error_code.API_20104_LOGIN_ERROR)
            # return
        user = Admin()
        user.username = username
        user.password = password
        user.id = usr.id
        user.role = usr.role
        token = self.get_access_token(user)
        return token, usr


class LoginView(CreateAPIView):
    authentication_classes = ()

    def post(self, request):
        usr = UserManager()
        value = value_judge(request, "username", "password")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        username = request.data.get('username')
        password = request.data.get('password')
        token, user = usr.login(username, password)
        return self.response({'code': 0, 'data': {'token': token, 'role': user.role_id}})


class PwdView(CreateAPIView):
    authentication_classes = (TokenAuthentication,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        value = value_judge(request, "password")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        new_pwd = request.data.get("password")
        user.password = UserManager.verify_pwd(new_pwd)
        user.role.updated_at = get_now()
        user.role.save()
        user.save()
        return self.response({'code': 0})


class CountView(RetrieveAPIView):
    def get(self, request, type, pk, cycle):
        start = request.GET.get('start')
        end = request.GET.get('end')
        if not verify_date(start) or not verify_date(end):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if type not in ['club', 'game'] or cycle not in ['d', 'w', 'm', 'y']:
            raise ParamErrorException(error_code.API_404_NOT_FOUND)
        if type == 'club':  # 按俱乐部分类
            club = Club.objects.get(id=pk)
            club_id = club.id
            coin_name = club.coin.name
            coin_id = club.coin_id

            # 用户充值，区块链余额
            recharge = ETH_Coin = UserRecharge.objects.filter(coin_id=coin_id).aggregate(Sum('amount')).get(
                "amount__sum")
            # 用户提现
            presentation = CoinDetail.objects.filter(sources=2, coin_name=coin_name).aggregate(Sum('amount')).get(
                "amount__sum")
            # 用户余额
            usercoin = UserCoin.objects.filter(coin_id=coin_id).aggregate(Sum('balance')).get('balance__sum')

            record = Record.objects.filter(option__club_id=club_id)

            # 平台统计表
            count_list = [] # 值列表
            key_list = [] # 键列表

            # 返回日期的统计
            time_list = get_range_time(cycle,start,end)

            # 分页处理，每次返回七条数据
            c = CountPage()
            time_list = c.paginate_queryset(queryset=time_list, request=request, view=self)


            for t in time_list:
                if cycle == 'd':  # 按天统计盈亏,键采用2018-06-06格式
                    key = str(t[0]).split(' ')[0]
                elif cycle == 'w':  # 按周统计盈亏,键采用2018-06-06/2018-06-12
                    key_prev = str(t[0]).split(' ')[0]
                    key_end = str(t[1]).split(' ')[0]
                    key = key_prev + '/' + key_end
                    pass
                elif cycle == 'm':  # 按月统计盈亏,键采用 2018-06
                    key = str(t[0]).split(' ')[0].split('-')
                    key = '-'.join([key[0], key[1]])

                else:  # 按年统计盈亏
                    key = str(t[0]).split(' ')[0].split('-')[0]
            #     bets = record.exclude(type=3).filter(open_prize_time__range=t).aggregate(Sum('bet')).get('bet__sum')
            #     bets_return = record.filter(type=1, open_prize_time__range=t).aggregate(Sum('bet')).get('bet__sum')
            #     if not bets: bets = 0
            #     if not bets_return: bets_return = 0
            #     earn = bets - bets_return
            #     earn = int(earn)
                count_list.append(0)
                key_list.append(key)

            bets_total = 0
            bets_return_total = 0
            total_earn = 0
            for item in record:  # 优化数据库请求
                if item.type != '3':
                    bets_total += item.bet
                if item.type == '1':
                    bets_return_total += item.bet
                if item.type == '2':
                    total_earn += item.bet
                    for d in time_list:
                        if  d[0]<=item.created_at<=d[1]:
                            count_list[time_list.index(d)] += item.bet
            count_list = map(int,count_list)
            time_earn_list = dict(zip(key_list,count_list))

            # # 下注总额
            # bets_total = record.exclude(type=3).aggregate(Sum('bet')).get('bet__sum')
            # # 下注发放额
            # bets_return_total = record.filter(type=1).aggregate(Sum('bet')).get('bet__sum')
            # # 平台总盈利
            # total_earn = bets_total - bets_return_total


            data = {
                'recharge': int(recharge),
                'ETH_Coin': int(ETH_Coin),
                'presentation': int(presentation),
                'usercoin': int(usercoin),
                'bets': int(bets_total),
                'bets_return': int(bets_return_total),
                'total_earn': int(total_earn),
                'count_list': time_earn_list
            }

            return self.response({'code': 0, 'data': data})
        else:  # 按游戏分类
            pass


class MassageView(ListAPIView):  # 没有独立的后台消息表，无法区分，pass
    def get_queryset(self):
        user_id = self.request.user.id
        list = UserMessage.objects.filter(Q(user_id=user_id), Q(message__type=1),
                                          Q(status=1) | Q(status=0)).order_by("status", "-created_at")
        return list

    def list(self, request, *args, **kwargs):
        data = []
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        for item in items:
            data.append({
                "user_message_id": item["id"],
                'message_title': item["title"],
                "status": item['status']
            })
        return self.response({'code': 0, 'data': data})


class MessageDetailView(ListAPIView):
    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        pass


class GSGView(RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        result = CoinDetail.objects.all()
        # 总资产
        total = 1000000000
        # 充值
        recharge = result.filter(sources=1, coin_name='GSG').aggregate(Sum('amount')).get("amount__sum")
        if not recharge: recharge = 0
        # 提现
        realisation = result.filter(sources=2, coin_name='GSG').aggregate(Sum('amount')).get("amount__sum")
        if not realisation: realisation = 0
        # 平台用户余额，user表integeal加上usercoin的余额,排除机器人
        integrals = User.objects.filter(is_robot=0).aggregate(Sum('integral')).get('integral__sum')
        balances = UserCoin.objects.filter(coin__name='GSG').aggregate(Sum('balance')).get('balance__sum')
        user_coin = float(integrals) + float(balances)
        # 区域链上余额
        ETH_balance = user_coin
        # 平台回收总额,类型为活动的并且值为负数
        recycle_GSG = result.filter(sources=4, amount__lt=0).aggregate(Sum('amount')).get("amount__sum")
        # 平台支出总额,返还+系统增加+活动正数
        activ = result.filter(sources=4, amount__lt=0).aggregate(Sum('amount')).get(
            "amount__sum")
        other = result.filter(sources=7).aggregate(Sum('amount')).get(
            "amount__sum")
        ret = result.filter(sources=9).aggregate(Sum('amount')).get(
            "amount__sum")
        pay_total = activ + other + ret

        # 计算占比支出
        activ_ratio = round(activ / pay_total, 4)
        other_ratio = round(other / pay_total, 4)
        ret_ratio = round(ret / pay_total, 4)

        ratio_dict = {'activ_ratio': activ_ratio, 'other_ratio': other_ratio,
                      'ret_ratio': ret_ratio}

        data = {
            'total': total,
            'recharge': recharge,
            'realisation': realisation,
            'user_coin': user_coin,
            'ETH_balance': ETH_balance,
            'recycle_GSG': recycle_GSG,
            'pay_total': pay_total,
            'ratio_dict': ratio_dict
        }

        return self.response({'code': 0, 'data': data})


