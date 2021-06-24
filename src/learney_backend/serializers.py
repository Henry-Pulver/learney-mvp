from rest_framework import serializers

from learney_backend.models import ContentLinkPreview, ContentVote


class LinkPreviewSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentLinkPreview
        fields = "__all__"


class VoteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentVote
        fields = "__all__"
