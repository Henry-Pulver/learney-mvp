from rest_framework import serializers

from learney_backend.models import ContentLinkPreview, ContentVote


class LinkPreviewSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentLinkPreview
        fields = "__all__"
        extra_kwargs = {"map_uuid": {"read_only": False}}


class VoteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentVote
        fields = "__all__"
        extra_kwargs = {"map_uuid": {"read_only": False}}
