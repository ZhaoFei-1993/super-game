from rest_framework import serializers
from users.models import GSGAssetAccount, Expenditure
from chat.models import Club, ClubRule

class GSGSerializer(serializers.HyperlinkedModelSerializer):
    """
    GSG账号表
    """

    class Meta:
        model = GSGAssetAccount
        fields = (
            "account_name", "chain_address", "account_type", "balance")


class ClubSerializer(serializers.HyperlinkedModelSerializer):
    room_title = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = (
            "id", "room_title", "icon")

    def get_room_title(self, obj):
        language = self.context['request'].GET.get('language')
        if language == 'en':
            room_title = obj.room_title_en
        else:
            room_title = obj.room_title
        return room_title


class GameSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = ClubRule
        fields = (
            "id", "title", "icon")

    def get_title(self, obj):
        language = self.context['request'].GET.get('language')
        if language == 'en':
            title = obj.title_en
        else:
            title = obj.title
        return title


class ExpenditureSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SerializerMethodField()
    in_out = serializers.SerializerMethodField()

    class Meta:
        model = Expenditure
        fields = (
            'year', 'month', 'type', 'in_out', 'amount', 'text')

    def get_type(self, obj):
        type = obj.type
        type = Expenditure.TYPE_CHOICE[int(type)][1]
        return type

    def get_in_out(self, obj):
        in_out = obj.in_out

        if not in_out:
            in_out = '支出'
        else:
            in_out = '收入'
        return in_out

class ClubRuleSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ClubRule
        fields = ("id", "title", "icon")
