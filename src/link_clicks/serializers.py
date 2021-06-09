from rest_framework import serializers
from link_clicks.models import LinkClickModel


class LinkClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkClickModel
        fields = '__all__'
