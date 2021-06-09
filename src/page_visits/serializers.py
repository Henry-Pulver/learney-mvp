from rest_framework import serializers
from page_visits.models import PageVisitModel


class PageVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageVisitModel
        fields = '__all__'
