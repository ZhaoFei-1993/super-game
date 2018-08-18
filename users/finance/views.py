from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView
from django.http import JsonResponse
from base.exceptions import UserLoginException
from rest_framework import status
from utils.functions import value_judge, reversion_Decorator, normalize_fraction
from rest_framework_jwt.settings import api_settings
import hashlib
from datetime import datetime, timedelta
from base import code as error_code
from base.exceptions import ParamErrorException
from wc_auth.models import Admin
import time
from .functions import get_now, get_range_time, verify_date, CountPage
from users.models import UserRecharge, UserPresentation, UserCoin, CoinDetail, UserMessage, User, FoundationAccount, \
    GSGAssetAccount, CoinOutServiceCharge, Expenditure
from chat.models import Club
from django.db.models import Sum, Q
from quiz.models import Record, OptionOdds, Quiz
from guess.models import Record as g_record
from users.finance.serializers import GSGSerializer, ClubSerializer, GameSerializer, ExpenditureSerializer, \
    ClubRuleSerializer
from users.app.v1.serializers import PresentationSerialize
import pytz
from sms.models import Sms
from django.conf import settings
from base.function import LoginRequired
from chat.models import ClubRule
from url_filter.integrations.drf import DjangoFilterBackend
from django.shortcuts import get_object_or_404


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
        try:
            user = Admin.objects.get(username=username)
            user.last_login = get_now()
            user.save()
        except Exception:
            raise UserLoginException(error_code=error_code.API_20103_TELEPHONE_UNREGISTER)
        # user = Admin()
        # user.username = username
        # user.password = password
        # user.id = usr.id
        # user.role = usr.role
        if user.check_password(password):
            token = self.get_access_token(user=user)
            return token, user
        else:
            raise UserLoginException(error_code=error_code.API_20104_LOGIN_ERROR)


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
        user.set_password(new_pwd)
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


class PresentView(ListAPIView):
    permission_classes = (LoginRequired,)
    queryset = UserPresentation.objects.all().order_by('-created_at')
    serializer_class = PresentationSerialize
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'status', 'coin', 'is_bill']

    def list(self, request, *args, **kwargs):
        items = super().list(request, *args, **kwargs)
        results = items.data.get('results')
        data = []
        for x in results:
            data.append({
                'id': x['id'],
                'amount': x['amount'],
                'coin_name': x['coin_name'],
                'user_name': x['user_name'],
                'status': x['status'],
                'created_at': x['created_at'],
                'is_bill': x['is_bill']
            })
        return self.response({'code': 0, 'data': data})


class PresentDetailView(ListCreateAPIView):
    # permission_classes = (LoginRequired,)

    def get(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        try:
            object = UserPresentation.objects.get(pk=pk)
        except Exception:
            return JsonResponse({'Error': '对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
        sers = PresentationSerialize(object).data
        data = {
            'id': sers['id'],
            'user_name': sers['user_name'],
            'coin_name': sers['coin_name'],
            'amount': sers['amount'],
            'is_block': sers['is_block'],
            'address': sers['address'],
            'status': sers['status'],
            'feedback': sers['feedback'],
            'txid': sers['txid'],
            'is_bill': sers['is_bill']
        }
        return self.response({'code': 0, 'data': data})

    # @reversion_Decorator
    def post(self, request, *args, **kwargs):
        id = kwargs['pk']  # 提现记录id
        if 'status' not in request.data \
                and 'feedback' not in request.data \
                and 'language' not in request.data:
            return JsonResponse({'Error': '请传递参数'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = UserPresentation.objects.get(pk=id)
        except Exception:
            return JsonResponse({'Error': 'Instance Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        if 'status' in request.data:
            sts = int(request.data.get('status'))
            item.status = sts
            if sts == 2:
                try:
                    user_coin = UserCoin.objects.get(user=item.user, coin=item.coin)
                    coin_out = CoinOutServiceCharge.objects.get(coin_out=user_coin.coin)
                except Exception:
                    raise
                if user_coin.coin.name == 'HAND':
                    try:
                        eth_coin = UserCoin.objects.get(user=item.user, coin__name='ETH')
                    except Exception:
                        raise
                    eth_coin.balance += coin_out.value
                    eth_coin.save()
                    user_coin.balance += item.amount
                else:
                    user_coin.balance = user_coin.balance + item.amount + coin_out.value
                user_coin.save()
                coin_detail = CoinDetail()
                coin_detail.user = user_coin.user
                coin_detail.name = user_coin.coin.name
                coin_detail.amount = item.amount
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.RETURN
                coin_detail.save()
                if 'feedback' in request.data:
                    text = request.data.get('feedback')
                    language = request.data.get('language', '')
                    item.feedback = text
                    user_message = UserMessage()
                    user_message.status = 0
                    if language == 'en':
                        user_message.content = 'Reason for:' + item.feedback
                        user_message.title = 'Present Reject'
                    else:
                        user_message.content = '拒绝提现理由:' + item.feedback
                        user_message.title = '提现失败公告'
                    user_message.user = item.user
                    user_message.message_id = 6  # 修改密码
                    user_message.save()
        item.save()
        return self.response({'code': 0})


class FinanceView(ListAPIView):
    # authentication_classes = ()
    serializer_class = ExpenditureSerializer
    permission_classes = (LoginRequired,)

    def paginate_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        type = self.request.GET.get('type')
        if not type:
            res = Expenditure.objects.all()
        else:
            res = Expenditure.objects.filter(type=type)
        return res

    def list(self, request, *args, **kwargs):
        items = super().list(request, *args, **kwargs)
        results = items.data.get('results')
        return self.response({'code': 0, 'data': results})


class BillView(ListCreateAPIView):
    """
    打款操作
    """

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        id = kwargs['pk']  # 提现记录id
        try:
            item = UserPresentation.objects.get(pk=id)
        except Exception:
            return JsonResponse({'Error': 'Instance Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        txid = '11111'
        state = 1
        if state == 1:
            item.is_bill = 1
            language = request.data.get('language', '')
            item.txid = txid
            user_message = UserMessage()
            user_message.status = 0
            if language == 'en':
                user_message.content = 'TXID:' + item.txid
                user_message.title = 'Present Success'
            else:
                user_message.content = 'TXID:' + item.txid
                user_message.title = '提现成功公告'
            user_message.user = item.user
            user_message.message_id = 6  # 修改密码
            user_message.save()
            item.save()
            return self.response({'code': 0})
        else:
            return JsonResponse({'Error': 'Present Fail'}, status=status.HTTP_400_BAD_REQUEST)

class PlayListView(ListAPIView):
    """
    玩法列表
    """
    queryset = ClubRule.objects.filter(is_deleted=0)
    serializer_class = ClubRuleSerializer


class PlayDetailView(RetrieveAPIView):
    """
    玩法详情
    """

    def retrieve(self, request, *args, **kwargs):
        play_id = int(kwargs['play_id'])
        play_item = get_object_or_404(ClubRule, pk=play_id)
        play_name = play_item.title
        data = list(self.play(play_name))
        return JsonResponse({'data':data}, status=status.HTTP_200_OK)

    @staticmethod
    def play(play_name):
        clubs = Club.objects.filter(coin__is_criterion=0).values('id','coin__name', 'coin__icon').order_by('coin__coin_order')
        ids = [x['id'] for x in clubs]
        now_date = datetime.now().date()
        day_ago = now_date - timedelta(1)
        week_ago = now_date - timedelta(7)
        if play_name == "球赛":
            quiz = Quiz.objects.filter(status=5).values('id').order_by('-id')
            quiz_ids = [x['id'] for x in quiz]
            bets = Record.objects.filter(open_prize_time__date__range=(week_ago, day_ago), roomquiz_id__in=ids,
                                         quiz_id__in=quiz_ids).extra(select={'date': 'date(open_prize_time)'}).extra({'club_id':'roomquiz_id'}).values(
                'date', 'club_id').annotate(sum_bets=Sum('bet')).order_by('date')
            earns = Record.objects.filter(open_prize_time__date__range=(week_ago, day_ago), roomquiz_id__in=ids,
                                          quiz_id__in=quiz_ids, earn_coin__gt=0).extra(
                select={'date': 'date(open_prize_time)'}).extra({'club_id':'roomquiz_id'}).values('date', 'club_id').annotate(
                sum_earn_coin=Sum('earn_coin')).order_by('date')

        if play_name == "猜股指":
            bets = g_record.objects.filter(open_prize_time__date__range=(week_ago, day_ago), club_id__in=ids,
                                           status=str(1)).extra(select={'date': 'date(open_prize_time)'}).values('date',
                                                                                                                 'club_id').annotate(
                sum_bets=Sum('bets')).order_by('date')
            earns = g_record.objects.filter(open_prize_time__date__range=(week_ago, day_ago), club_id__in=ids,
                                            status=str(1), earn_coin__gt=0).extra(
                select={'date': 'date(open_prize_time)'}).values('date', 'club_id').annotate(
                sum_earn_coin=Sum('earn_coin')).order_by('date')
        temp_bets = {}
        temp_earns= {}
        format = '%m/%d'
        if len(bets) > 0:
            for c in bets:
                date = c['date'].strftime(format)
                if str(c['club_id']) not in temp_bets:
                    temp_bets[str(c['club_id'])]={}
                temp_bets[str(c['club_id'])][str(date)]=c['sum_bets']
        if len(earns) > 0:
            for d in earns:
                date = d['date'].strftime(format)
                if str(d['club_id']) not in temp_earns:
                    temp_earns[str(d['club_id'])]={}
                temp_earns[str(d['club_id'])][date]=d['sum_earn_coin']
        for a in clubs:
            a['start_day'] = week_ago.strftime('%Y-%m-%d')
            a['end_day'] = day_ago.strftime('%Y-%m-%d')
            for b in range(0,7):
                date = (week_ago + timedelta(b)).strftime(format)
                day_ago_date = day_ago.strftime(format)
                temp_none = {'date': date, 'profit': 0}
                if temp_bets:
                    if str(a['id']) not in temp_bets:
                        if date == day_ago_date:
                            a['in'] = 0
                            a['out'] = 0
                            a['last_profit'] = 0
                        if 'results' not in a:
                            a['results'] = [temp_none]
                        else:
                            a['results'].append(temp_none)
                    else:
                        if date in temp_bets[str(a['id'])]:
                            if str(a['id']) not in temp_earns:
                                if 'results' not in a:
                                    a['results']=[{'date':date, 'profit':normalize_fraction(temp_bets[str(a['id'])][date],4)}]
                                else:
                                    a['results'].append({'date':date, 'profit':normalize_fraction(temp_bets[str(a['id'])][date],4)})
                                if date == day_ago_date:
                                    a['in'] = normalize_fraction(temp_bets[str(a['id'])][date],4)
                                    a['out'] = 0
                                    a['last_profit'] = normalize_fraction(temp_bets[str(a['id'])][date],4)
                            else:
                                if date not in temp_earns[str(a['id'])]:
                                    if 'results' not in a:
                                        a['results'] = [{'date': date, 'profit': normalize_fraction(temp_bets[str(a['id'])][date],4)}]
                                    else:
                                        a['results'].append({'date': date, 'profit': normalize_fraction(temp_bets[str(a['id'])][date],4)})
                                    if date == day_ago_date:
                                        a['in'] = normalize_fraction(temp_bets[str(a['id'])][date], 4)
                                        a['out'] = 0
                                        a['last_profit'] = normalize_fraction(temp_bets[str(a['id'])][date], 4)
                                else:
                                    if 'results' not in a:
                                        a['results'] = [{'date': date, 'profit': normalize_fraction(temp_bets[str(a['id'])][date] - temp_earns[str(a['id'])][date],4)}]
                                    else:
                                        a['results'].append({'date': date, 'profit': normalize_fraction(temp_bets[str(a['id'])][date] - temp_earns[str(a['id'])][date],4)})
                                    if date == day_ago_date:
                                        a['in'] = normalize_fraction(temp_bets[str(a['id'])][date], 4)
                                        a['out'] = normalize_fraction(temp_earns[str(a['id'])][date], 4)
                                        a['last_profit'] = normalize_fraction(temp_bets[str(a['id'])][date] - temp_earns[str(a['id'])][date],4)
                        else:
                            if 'results' not in a:
                                a['results'] = [temp_none]
                            else:
                                a['results'].append(temp_none)
                            if date == day_ago_date:
                                a['in'] = 0
                                a['out'] = 0
                                a['last_profit'] = 0
                else:
                    if 'results' not in a:
                        a['results'] = [temp_none]
                    else:
                        a['results'].append(temp_none)
                    if date == day_ago_date:
                        a['in'] = 0
                        a['out'] = 0
                        a['last_profit'] = 0
        return clubs




