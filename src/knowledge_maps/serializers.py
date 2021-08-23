from rest_framework import serializers

from knowledge_maps.models import KnowledgeMapModel


class KnowledgeMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeMapModel
        fields = "__all__"
