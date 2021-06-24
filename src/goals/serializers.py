from rest_framework import serializers

from goals.models import GoalModel


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalModel
        fields = "__all__"
