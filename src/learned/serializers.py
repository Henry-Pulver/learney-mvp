from rest_framework import serializers

from learned.models import LearnedModel


class LearnedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnedModel
        fields = "__all__"
        extra_kwargs = {"map_uuid": {"read_only": False}}
