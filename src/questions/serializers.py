from rest_framework import serializers

from questions.models import QuestionResponse


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResponse
        fields = "__all__"
        read_only_fields = ("id",)
