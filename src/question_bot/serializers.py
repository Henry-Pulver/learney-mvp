from rest_framework import serializers

from question_bot.models import AnswerModel, SlackBotUserModel


class SlackBotUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackBotUserModel
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerModel
        fields = "__all__"
