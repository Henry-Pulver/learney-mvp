from rest_framework import serializers

from learney_backend.models import ContentVote


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentVote
        fields = "__all__"
