from rest_framework import serializers

from questions.models import QuestionResponseModel


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResponseModel
        fields = "__all__"
        read_only_fields = ("id",)
