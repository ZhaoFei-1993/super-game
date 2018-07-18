from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView
from django.http import JsonResponse
# from users.finance.authentications import CCSignatureAuthentication
from utils.functions import value_judge
from rest_framework_jwt.settings import api_settings
import hashlib
from datetime import datetime
from base import code as error_code
from base.exceptions import ParamErrorException
from wc_auth.models import Admin
import time
from .functions import get_now, get_range_time, verify_date, CountPage
from users.models import UserRecharge, UserPresentation, UserCoin, CoinDetail, UserMessage, User, FoundationAccount, \
    GSGAssetAccount
from chat.models import Club
from django.db.models import Sum, Q
from quiz.models import Record, OptionOdds
from users.finance.serializers import GSGSerializer, ClubSerializer, GameSerializer
import pytz
from sms.models import Sms
from django.conf import settings
from base.function import LoginRequired
from chat.models import ClubRule


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
            user = Admin.objects.get(username=username, password=password)
            user.last_login = get_now()
            user.save()
        except:
            raise ParamErrorException(error_code.API_20104_LOGIN_ERROR)
            # return
        # user = Admin()
        # user.username = username
        # user.password = password
        # user.id = usr.id
        # user.role = usr.role
        token = self.get_access_token(user)
        return token, user


class LoginView(CreateAPIView):
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
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        value = value_judge(request, "password", "telephone")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        area_code = 86

        if "telephone" not in request.data:
            message = Sms.objects.filter(code=request.data.get('code'), type=7).first()
        else:
            message = Sms.objects.filter(area_code=area_code, telephone=request.data.get('telephone'),
                                         code=request.data.get('code'), type=7).first()
        if not message:
            raise ParamErrorException(error_code.API_40106_SMS_PARAMETER)
        if int(message.degree) >= 5:
            raise ParamErrorException(error_code.API_40107_SMS_PLEASE_REGAIN)
        else:
            message.degree += 1
            message.save()

        # 短信发送时间
        code_time = message.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
        code_time = time.mktime(code_time.timetuple())
        current_time = time.mktime(datetime.now().timetuple())

        # 判断code_id有效性
        if message is None:
            raise ParamErrorException(error_code.API_40101_SMS_CODE_ID_INVALID)

        # 判断code有效性
        if message.code != request.data.get('code'):
            raise ParamErrorException(error_code.API_40103_SMS_CODE_INVALID)

        # 判断code是否过期
        if (settings.SMS_CODE_EXPIRE_TIME > 0) and (current_time - code_time > settings.SMS_CODE_EXPIRE_TIME):
            raise ParamErrorException(error_code.API_40102_SMS_CODE_EXPIRED)

        # 若校验通过，则更新短信发送记录表状态为校验通过
        message.is_passed = True
        message.save()

        new_pwd = request.data.get("password")
        user.password = UserManager.verify_pwd(new_pwd)
        user.role.updated_at = get_now()
        user.role.save()
        user.save()
        return self.response({'code': 0})


class CountView(RetrieveAPIView):
    permission_classes = (LoginRequired,)

    def get(self, request, type, pk):
        if type not in ['club', 'game']:
            raise ParamErrorException(error_code.API_404_NOT_FOUND)
        if type == 'club':  # 按俱乐部分类
            club = Club.objects.get(id=pk)
            club_id = club.id
            coin_name = club.coin.name
            coin_id = club.coin_id

            # 用户充值，区块链余额
            recharge = ETH_Coin = UserRecharge.objects.filter(coin_id=coin_id).aggregate(Sum('amount')).get(
                "amount__sum")
            if not recharge: recharge = 0;ETH_Coin = 0
            # 用户提现
            presentation = CoinDetail.objects.filter(sources=2, coin_name=coin_name).aggregate(Sum('amount')).get(
                "amount__sum", 0)
            if not presentation: presentation = 0
            # 用户余额
            usercoin = UserCoin.objects.filter(coin_id=coin_id).aggregate(Sum('balance')).get('balance__sum', 0)
            if not usercoin: usercoin = 0

            data = {
                'recharge': int(recharge),
                'ETH_Coin': int(ETH_Coin),
                'presentation': int(presentation),
                'usercoin': int(usercoin),
            }

            return self.response({'code': 0, 'data': data})
        else:  # 按游戏分类
            pass


class BetCountView(RetrieveAPIView):
    # authentication_classes = ()
    permission_classes = (LoginRequired,)

    def get(self, request, type, pk):
        if type not in ['club', 'game']:
            raise ParamErrorException(error_code.API_404_NOT_FOUND)
        record = Record.objects.filter(option__club_id=pk)

        # 下注总额
        bets_total = record.exclude(type=3).aggregate(Sum('bet')).get('bet__sum', 0)
        if not bets_total: bets_total = 0
        # 下注发放额
        bets_return_total = record.filter(type=1).aggregate(Sum('bet')).get('bet__sum', 0)
        if not bets_return_total: bets_return_total = 0
        # 平台总盈利
        total_earn = bets_total - bets_return_total

        data = {
            'bets': int(bets_total),
            'bets_return': int(bets_return_total),
            'total_earn': int(total_earn),
        }
        return self.response({'code': 0, 'data': data})


class DateCountView(ListAPIView):
    permission_classes = (LoginRequired,)

    def get_queryset(self, *args, **kwargs):
        print(args, kwargs)
        return {'1': 1}

    def list(self, request, type, pk):
        cycle = request.GET.get('cycle')
        start = request.GET.get('start')
        end = request.GET.get('end')
        if not verify_date(start) or not verify_date(end) or cycle not in ['d', 'w', 'm', 'y'] or type not in ['club',
                                                                                                               'game']:
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

        # 平台统计表
        count_list = []  # 值列表
        key_list = []  # 键列表

        # 返回日期的统计
        time_list = get_range_time(cycle, start, end)[::-1]

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
            # count_list.append(0)
            key_list.append(key)

        if type == 'club':
            club = Club.objects.get(id=pk)
            club_id = club.id
            print(club_id)
            record = Record.objects.filter(option__club_id=club_id, type=2)
            for d in time_list:
                bet = record.filter(created_at__lte=d[1], created_at__gte=d[0]).aggregate(Sum('bet')).get('bet__sum')
                if not bet:
                    bet = 0
                count_list.append(int(bet))
        return self.response({'code': 0, 'data': [key_list, count_list]})


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
    permission_classes = (LoginRequired,)

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
        balances = UserCoin.objects.filter(coin__name='GSG').aggregate(Sum('balance')).get('balance__sum')
        user_coin = float(balances)
        # 区域链上余额
        ETH_balance = user_coin
        # 平台回收总额,类型为活动的并且值为负数
        recycle_GSG = result.filter(sources=4, amount__lt=0).aggregate(Sum('amount')).get("amount__sum")
        # 平台支出总额,返还+系统增加+活动正数
        activ = result.filter(sources=4, amount__lt=0).aggregate(Sum('amount')).get(
            "amount__sum")
        if not activ: activ = 0
        other = result.filter(sources=7).aggregate(Sum('amount')).get(
            "amount__sum")
        if not other: other = 0
        ret = result.filter(sources=9).aggregate(Sum('amount')).get(
            "amount__sum")
        if not ret: ret = 0
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


class SharesView(ListAPIView):
    permission_classes = (LoginRequired,)
    serializer_class = GSGSerializer

    def get_queryset(self):
        res = GSGAssetAccount.objects.filter(account_type=1)
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        total_balance = GSGAssetAccount.objects.filter(account_type=1).aggregate(Sum('balance')).get("balance__sum")
        res_list = []
        for i in items:
            res_dict = {}
            res_dict['name'] = i['account_name']
            value = round(float(i['balance']) / float(total_balance), 4) * 100
            res_dict['data'] = value
            res_list.append(res_dict)
        return self.response({'code': 0, 'data': res_list})


class FootstoneView(ListAPIView):
    permission_classes = (LoginRequired,)

    def queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        res = FoundationAccount.objects.values('type', 'coin__name', 'coin__icon').annotate(Sum('balance')).order_by(
            'coin')
        footstone_list = []
        ICO_list = []
        private_list = []

        for i in res:
            i['balance__sum'] = int(i['balance__sum'])
            print(i)
            if i['type'] == '0':  # 基石
                footstone_list.append(i)
            if i['type'] == '1':  # ICO
                ICO_list.append(i)
            if i['type'] == '2':  # 私募
                private_list.append(i)
        data = {
            'footstone': footstone_list,
            'ICO': ICO_list,
            'private': private_list
        }
        return self.response({'code': 0, 'data': data})


class ClubView(ListAPIView):
    permission_classes = (LoginRequired,)
    serializer_class = ClubSerializer

    def get_queryset(self):
        res = Club.objects.all()
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        res = results.data.get('results')

        return self.response({'code': 0, 'data': res})


class GameView(ListAPIView):
    permission_classes = (LoginRequired,)
    serializer_class = GameSerializer

    def get_queryset(self):
        res = ClubRule.objects.all()
        return res

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        res = results.data.get('results')
        return self.response({'code': 0, 'data': res})
