# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import StockListSerialize, GuessPushSerializer, PlayListSerializer
from ...models import Stock, Record

class StockList(ListAPIView):
    """
    股票列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = StockListSerialize

    def get_queryset(self):
        stock_list = Stock.objects.all()
        return stock_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for list in items:
            data.append({
                "id": list["pk"],
                "periods_id": list["periods_id"],
                "title": list["title"],
                "periods": list["periods"],
                "closing_time": list["closing_time"],
                "previous_result": list["previous_result"],
                "previous_result_colour": list["previous_result_colour"],
                "index": list["index"],
                "index_colour": list["index_colour"],
                "rise": list["rise"],
                "fall": list["fall"]
            })

        return self.response({'code': 0, 'data': data})


class GuessPushView(ListAPIView):
    """
    详情页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = GuessPushSerializer

    def get_queryset(self):
        club_id = self.request.GET.get('club_id')
        periods_id = self.request.GET.get('periods_id')
        record = Record.objects.filter(club_id=club_id, periods_id=periods_id)
        return record

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "username": item['username'],
                    "my_play": item['my_play'],
                    "my_option": item['my_option'],
                    "bet": item['bet']
                }
            )
        return self.response({"code": 0, "data": data})


class PlayView(ListAPIView):
    """
    股票选项
    """
    permission_classes = (LoginRequired,)
    serializer_class = PlayListSerializer