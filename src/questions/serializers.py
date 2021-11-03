from rest_framework import serializers

from questions.models import QuestionConceptTagModel, QuestionModel, QuestionResponseModel


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionModel
        fields = "__all__"
        extra_kwargs = {"tags": {"required": True}}
        read_only_fields = ("id", "time_written")


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResponseModel
        fields = "__all__"
        read_only_fields = ("id", "time_asked")
