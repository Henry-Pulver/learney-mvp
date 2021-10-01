from rest_framework import serializers

from button_presses.models import ButtonPressModel


class ButtonPressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ButtonPressModel
        fields = "__all__"
        read_only_fields = ("id", "timestamp")
