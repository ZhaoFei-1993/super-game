from rest_framework import serializers
from users.models import GSGAssetAccount

class GSGSerializer(serializers.HyperlinkedModelSerializer):
    """
    GSG账号表
    """
    class Meta:
        model = GSGAssetAccount
        fields = (
            "account_name","chain_address","account_type","balance")