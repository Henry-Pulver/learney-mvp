from rest_framework import serializers

from goals.models import GoalModel


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalModel
        fields = "__all__"
        extra_kwargs = {"map_uuid": {"read_only": False}}
