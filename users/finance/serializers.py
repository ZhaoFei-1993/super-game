from rest_framework import serializers
from users.models import GSGAssetAccount
from chat.models import Club,ClubRule

class GSGSerializer(serializers.HyperlinkedModelSerializer):
    """
    GSG账号表
    """
    class Meta:
        model = GSGAssetAccount
        fields = (
            "account_name","chain_address","account_type","balance")


class ClubSerializer(serializers.HyperlinkedModelSerializer):

    room_title = serializers.SerializerMethodField()
    class Meta:
        model = Club
        fields = (
            "id", "room_title", "icon")

    def get_room_title(self,obj):
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

    def get_title(self,obj):
        language = self.context['request'].GET.get('language')
        if language == 'en':
            title = obj.title_en
        else:
            title = obj.title
        return title